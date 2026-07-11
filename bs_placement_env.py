import numpy as np
import json
import gymnasium as gym
from gymnasium import spaces
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from stable_baselines3.common.callbacks import BaseCallback
import matplotlib.pyplot as plt

with open(r"C:\Users\sarah\OneDrive\Desktop\BS\campus_polygons_local_meters.json") as f:
    raw_polygons = json.load(f)

building_polygon = Polygon(raw_polygons["DBuilding"])
valid_area_1 = Polygon(raw_polygons["ValidArea1"])
valid_area_2 = Polygon(raw_polygons["ValidArea2"])
valid_region = unary_union([valid_area_1, valid_area_2])

CANDIDATE_SPACING = 3.0
minx_b, miny_b, maxx_b, maxy_b = building_polygon.bounds
gx = np.arange(minx_b, maxx_b, CANDIDATE_SPACING)
gy = np.arange(miny_b, maxy_b, CANDIDATE_SPACING)
BS_CANDIDATES = np.array([
    (x, y) for x in gx for y in gy if building_polygon.contains(Point(x, y))
])

BS_HEIGHT = 12.0
BS_HEIGHTS = np.full(len(BS_CANDIDATES), BS_HEIGHT)
N_CANDIDATES = len(BS_CANDIDATES)

minx, miny, maxx, maxy = valid_region.union(building_polygon).bounds


def sample_user_point():
    while True:
        x = np.random.uniform(minx, maxx)
        y = np.random.uniform(miny, maxy)
        if valid_region.contains(Point(x, y)):
            return x, y

COVERAGE_THRESHOLD = 1.0  # minimum acceptable rate (bits/s/Hz) to count as "covered"

def compute_metrics(bs_x, bs_y, bs_h, user_positions):

    horizontal_distances = np.sqrt(
        np.sum((user_positions - np.array([bs_x, bs_y])) ** 2, axis=1)
    )
    vertical_distance = bs_h - USER_HEIGHT
    distances = np.sqrt(horizontal_distances ** 2 + vertical_distance ** 2)
    snr_values = P_tx / ((distances ** alpha) * N0)
    per_user_rates = np.log2(1 + snr_values)

    n = len(per_user_rates)
    jains_index = (np.sum(per_user_rates) ** 2) / (n * np.sum(per_user_rates ** 2))
    coverage_pct = 100.0 * np.mean(per_user_rates >= COVERAGE_THRESHOLD)

    return per_user_rates, jains_index, coverage_pct


P_tx = 1.0
N0 = 1e-10
alpha = 4
USER_HEIGHT = 2.0
K = 2000 # number of users


class DBuildingPlacementEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.K = K
        self.action_space = spaces.Discrete(N_CANDIDATES)
        self.observation_space = spaces.Box(
            low=-200, high=200, shape=(2 * self.K,), dtype=np.float32
        )
        self.user_positions = None
        self.first_episode = True

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        if self.first_episode or self.user_positions is None:
            self.user_positions = np.array([sample_user_point() for _ in range(self.K)])
            self.first_episode = False
        return self.user_positions.flatten().astype(np.float32), {}

    def step(self, action):
        bs_x, bs_y = BS_CANDIDATES[action]
        bs_h = BS_HEIGHTS[action]

        horizontal_distances = np.sqrt(
            np.sum((self.user_positions - np.array([bs_x, bs_y])) ** 2, axis=1)
        )
        vertical_distance = bs_h - USER_HEIGHT
        distances = np.sqrt(horizontal_distances ** 2 + vertical_distance ** 2)

        snr_values = P_tx / ((distances ** alpha) * N0)
        reward = np.min(np.log2(1 + snr_values))  # max-min fairness, same as sample code

        terminated = False
        truncated = False
        info = {"bs_x": bs_x, "bs_y": bs_y, "bs_height": bs_h}
        return self.user_positions.flatten().astype(np.float32), reward, terminated, truncated, info

    def render(self, mode="human"):
        pass
# Sanity check: random policy baseline (Step 5 from our checklist)

if __name__ == "__main__":
    from stable_baselines3 import DQN

    env = DBuildingPlacementEnv()
    obs, info = env.reset()
    print(f"Observation shape: {obs.shape} (expected {2*K},)")
    print(f"Action space size: {env.action_space.n}")

    rewards = []
    for _ in range(500):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        rewards.append(reward)

    rewards = np.array(rewards)
    print(f"\nRandom policy over 500 steps:")
    print(f"  min reward:  {rewards.min():.3f}")
    print(f"  mean reward: {rewards.mean():.3f}")
    print(f"  max reward:  {rewards.max():.3f}")
    print(f"  any NaN/inf: {np.any(~np.isfinite(rewards))}")

    print("\n--- Training DQN ---")
    train_env = DBuildingPlacementEnv()

    class RewardCallback(BaseCallback):
        def __init__(self, verbose=0):
            super().__init__(verbose)
            self.episode_rewards = []  # every reward, for the training curve plot
            self.best_overall_reward = -np.inf
            self.best_action = None

        def _on_step(self) -> bool:
            reward = self.locals['rewards'][0]
            action = self.locals['actions'][0]

            self.episode_rewards.append(reward)

            if reward > self.best_overall_reward:
                self.best_overall_reward = reward
                self.best_action = int(action)

            return True

    model = DQN(
        "MlpPolicy",
        train_env,
        learning_rate=5e-4,
        buffer_size=20000,
        batch_size=64,
        train_freq=1,
        verbose=0,
    )
    callback = RewardCallback()
    model.learn(total_timesteps=20000, callback=callback)

    # Evaluate the trained policy greedily over the same fixed users
    eval_env = DBuildingPlacementEnv()
    obs, info = eval_env.reset()
    eval_env.user_positions = train_env.user_positions  # same users as training
    trained_rewards = []
    for action in range(N_CANDIDATES):
        obs, reward, terminated, truncated, info = eval_env.step(action)
        trained_rewards.append(reward)

    trained_rewards = np.array(trained_rewards)
    best_action = np.argmax(trained_rewards)
    print(f"\nBest achievable reward (brute force over all {N_CANDIDATES} candidates): "
          f"{trained_rewards.max():.3f}")
    print(f"Worst reward: {trained_rewards.min():.3f}")

    predicted_action, _ = model.predict(obs, deterministic=True)
    predicted_action = int(predicted_action)
    print(f"\nDQN's chosen action after training: {predicted_action}")
    print(f"DQN's chosen reward: {trained_rewards[predicted_action]:.3f}")
    print(f"Gap to best-possible: {trained_rewards.max() - trained_rewards[predicted_action]:.3f}")

    print(f"\nBest EVER seen during training: action {callback.best_action}, "
          f"reward {callback.best_overall_reward:.3f}")
    if callback.best_overall_reward > trained_rewards[predicted_action]:
        print(f"\n-> Best-seen-during-training beats the final policy. "
              f"Using action {callback.best_action} instead.")
        predicted_action = callback.best_action
    else:
        print(f"\n-> Final policy's answer is already the best we found. Keeping it.")


    best_x, best_y = BS_CANDIDATES[predicted_action]
    best_height = BS_HEIGHTS[predicted_action]

    print("\n=== BEST BS LOCATION (what you actually report) ===")
    print(f"  Position (local meters): x = {best_x:.2f}, y = {best_y:.2f}")
    print(f"  Mount height: {best_height:.1f} m")
    print(f"  Reward achieved: {trained_rewards[predicted_action]:.3f}")

    per_user_rates, jains_index, coverage_pct = compute_metrics(
        best_x, best_y, best_height, train_env.user_positions
    )
    print(f"\n=== EVALUATION METRICS ===")
    print(f"  Jain's fairness index: {jains_index:.4f}  (1.0 = perfectly fair)")
    print(f"  Coverage: {coverage_pct:.1f}%  (users above {COVERAGE_THRESHOLD} bits/s/Hz)")
    print(f"  Mean rate across users: {per_user_rates.mean():.3f}")

    # --- Training curve ---
    window = 100
    if len(callback.episode_rewards) >= window:
        smoothed = np.convolve(callback.episode_rewards, np.ones(window) / window, mode='valid')
    else:
        smoothed = callback.episode_rewards

    plt.figure(figsize=(8, 5))
    plt.plot(smoothed)
    plt.xlabel("Training step")
    plt.ylabel("Reward (smoothed)")
    plt.title("DQN training reward over time")
    plt.grid(True, alpha=0.3)
    plt.savefig("training_curve.png", dpi=150)
    print("\nSaved training_curve.png")

    # --- Final placement plot ---
    fig, ax = plt.subplots(figsize=(8, 8))
    bx, by = building_polygon.exterior.xy
    ax.fill(bx, by, color="tab:gray", alpha=0.5, label="D Building")

    if valid_region.geom_type == "Polygon":
        vx, vy = valid_region.exterior.xy
        ax.fill(vx, vy, color="tab:blue", alpha=0.15, label="Valid region")
    else:
        for geom in valid_region.geoms:
            vx, vy = geom.exterior.xy
            ax.fill(vx, vy, color="tab:blue", alpha=0.15)

    users = train_env.user_positions
    ax.scatter(users[:, 0], users[:, 1], c="tab:green", s=30, edgecolors="black", label="Users", zorder=4)
    ax.scatter(best_x, best_y, c="red", marker="*", s=400, edgecolors="black", label="Chosen BS location", zorder=5)
    ax.set_xlabel("X (meters)")
    ax.set_ylabel("Y (meters)")
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(f"Final BS placement (reward = {trained_rewards[predicted_action]:.2f})")
    ax.grid(True, alpha=0.3)
    plt.savefig("final_placement.png", dpi=150)
    print("Saved final_placement.png")