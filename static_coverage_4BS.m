Codes 
clear tx rx viewer
close(findall(0,'Type','figure'))
viewer = siteviewer("Buildings", "map.osm", "Basemap", "openstreetmap");
tx(1) = txsite("Name","BS_A","Latitude", 29.985361, "Longitude", 31.441287, "AntennaHeight", 20, "TransmitterFrequency", 2.5e9);  % A
tx(2) = txsite("Name","BS_B","Latitude", 29.985331, "Longitude", 31.438954, "AntennaHeight", 20, "TransmitterFrequency", 2.5e9);  % B
tx(3) = txsite("Name","BS_C","Latitude", 29.986716, "Longitude", 31.438956, "AntennaHeight", 20, "TransmitterFrequency", 2.5e9);  % C
tx(4) = txsite("Name","BS_D","Latitude", 29.986700, "Longitude", 31.441365, "AntennaHeight", 20, "TransmitterFrequency", 2.5e9);  % D
show(tx)
usr = [29.985132 31.440892;  29.984831 31.441494;  29.985188 31.441841;  29.985633 31.440941;  29.985576 31.441615;   % A
      29.984935 31.438786;  29.985229 31.438422;  29.985130 31.439388;  29.985750 31.438700;  29.985816 31.439382;   % B
      29.986456 31.438658;  29.986475 31.438239;  29.986434 31.439369;  29.987000 31.439319;  29.987202 31.438534;   % C
      29.986502 31.441034;  29.986491 31.441631;  29.986970 31.441658;  29.987028 31.442144;  29.986995 31.440868];  % D
grp = repelem(["A";"B";"C";"D"], 5);           
num = repmat((1:5)', 4, 1);                    
rx = rxsite("Name","User_"+grp+num, ...
           "Latitude",usr(:,1), "Longitude",usr(:,2), ...
           "AntennaHeight",1.5);
show(rx)
pm = propagationModel("raytracing", "Method", "sbr", "MaxNumReflections", 3);
for g = 1:4
   rxIdx = (g-1)*5 + (1:5);    
   raytrace(tx(g), rx(rxIdx), pm)
end
coverage(tx, pm)
