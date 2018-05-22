set title "Supported devices per day"
set xdata time
set style data lines
set term png
set timefmt "%Y-%m-%d %H:%M:%S"
set format x "%Y-%m-%d"
set xlabel "Days"
set ylabel "Devices"
set autoscale y
set output "devices.png"
set datafile separator "\t"
plot "chart.dat" using 1:2