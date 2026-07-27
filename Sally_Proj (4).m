%% Section 1: Load the indoor scene
viewer = siteviewer(SceneModel="office.stl", ShowOrigin=false, Transparency=0.25);
%% Section 2: Place transmitter and receivers
tx = txsite("cartesian", AntennaPosition=[2; 1.3; 2.5]);      
rx_desk = rxsite("cartesian", AntennaPosition=[3.6; 7.5; 1]); 
rx_shelf = rxsite("cartesian", AntennaPosition=[0.4; 3.3; 1]);
show(tx)
show(rx_desk)
show(rx_shelf)
los(tx, [rx_desk rx_shelf])
pm = propagationModel("raytracing", CoordinateSystem="cartesian", SurfaceMaterial="wood");
reflectionLevels = 0:3;
receivedPower_desk = zeros(size(reflectionLevels));
receivedPower_shelf = zeros(size(reflectionLevels));
for i = 1:length(reflectionLevels)
   pm.MaxNumReflections = reflectionLevels(i);
   receivedPower_desk(i) = sigstrength(rx_desk, tx, pm);
   receivedPower_shelf(i) = sigstrength(rx_shelf, tx, pm);
   fprintf("Reflections=%d -> Desk=%.2f dBm | Shelf=%.2f dBm\n", ...
       reflectionLevels(i), receivedPower_desk(i), receivedPower_shelf(i));
end
figure
plot(reflectionLevels, receivedPower_desk, '-o', 'DisplayName', 'Desk (blocked)')
hold on
plot(reflectionLevels, receivedPower_shelf, '-s', 'DisplayName', 'Shelf (line of sight)')
hold off
xlabel('Max Number of Reflections')
ylabel('Received Power (dBm)')
title('Effect of Reflections on Received Power')
legend
grid on
pm = propagationModel("raytracing", CoordinateSystem="cartesian", SurfaceMaterial="wood");
% --- Case 1: Reflection only ---
pm.MaxNumReflections = 1;
pm.MaxNumDiffractions = 0;
clearMap(viewer)
raytrace(tx, rx_desk, pm)
ss_reflectionOnly = sigstrength(rx_desk, tx, pm);
fprintf("Reflection only  -> %.2f dBm\n", ss_reflectionOnly);
% --- Case 2: Diffraction only ---
pm.MaxNumReflections = 0;
pm.MaxNumDiffractions = 1;
clearMap(viewer)
raytrace(tx, rx_desk, pm)
ss_diffractionOnly = sigstrength(rx_desk, tx, pm);
fprintf("Diffraction only -> %.2f dBm\n", ss_diffractionOnly);
% --- Case 3: Combined ---
pm.MaxNumReflections = 1;
pm.MaxNumDiffractions = 1;
clearMap(viewer)
raytrace(tx, rx_desk, pm)
ss_combined = sigstrength(rx_desk, tx, pm);
fprintf("Combined         -> %.2f dBm\n", ss_combined);
%% Section 7: Bar chart comparing the three cases
figure
bar(categorical({'Reflection Only','Diffraction Only','Combined'}), ...
   [ss_reflectionOnly, ss_diffractionOnly, ss_combined])
ylabel('Received Power (dBm)')
title('Desk Receiver: Reflection vs Diffraction vs Combined')
grid on

