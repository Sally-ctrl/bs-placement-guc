clear; 
viewer = siteviewer("Buildings","map.osm");

tx = txsite("Name","BS_C","Latitude",29.986855,"Longitude",31.438944, ...
            "AntennaHeight",12,"TransmitterFrequency",2.5e9);
show(tx)

% ---- Users: start positions + headings ----
lat0 = [29.986434; 29.987000; 29.987202];
lon0 = [31.439319; 31.439319; 31.438534];
hdg  = [160; 90; 300];    
speed = 1.4;                 % m/s
noise = 1e-5;
T = 25;                    % seconds
Pt_dBm = 70;                    % transmit power, dBm (typical small-cell value)
Pt = 10^((Pt_dBm-30)/10);       % convert dBm to Watts
rx = rxsite("Name","User_"+(1:3)', ...
            "Latitude",lat0,"Longitude",lon0,"AntennaHeight",1.5);

pm = propagationModel("raytracing","Method","sbr","MaxNumReflections",3);

rates = zeros(T+1, 3);
sumRate = zeros(T+1, 1);
-
for k = 1:T+1
    time = k-1;
    d = speed*time;
    lat = lat0 + d*cosd(hdg)/111320;
    lon = lon0 + d*sind(hdg)./(111320*cosd(lat0));

    for u = 1:3
        rx(u).Latitude  = lat(u);
        rx(u).Longitude = lon(u);
    end

    clearMap(viewer)
    show(tx); show(rx)

    rays = raytrace(tx, rx, pm);       

    for u = 1:3
        r = rays{u};
        if isempty(r)
            h = 0;                     
        else
            plot(r)                   
            h = sum(10.^(-[r.PathLoss]/20) .* exp(1j*[r.PhaseShift]));
        end
        snr = Pt * abs(h)^2 / noise;
        rates(k,u) = log2(1 + snr);
    end
    sumRate(k) = sum(rates(k,:));

    pause(0.3)
end

% ---- Results plot ----
figure
plot(0:T, rates, '-o'); hold on
plot(0:T, sumRate, 'Color', [0.85 0.33 0.10], 'LineWidth', 2)  
legend("User 1","User 2","User 3","Sum rate")
xlabel("Time (s)"); ylabel("Rate (bps/Hz)")
title("User rates and sum rate vs time — linear mobility")
set(gcf,"Color","white")    % figure background
set(gca,"Color","white")    % axes background
set(gca, "XColor", "black", "YColor", "black")
set(gca, "GridColor", [0.15 0.15 0.15])   
grid on
