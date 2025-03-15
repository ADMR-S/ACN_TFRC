set terminal png
set output "Plot_10Mbps_7ms_0loss.png"
set xlabel "TIme (s)"
set ylabel "Bandwidth reports server-side (Mbps)"
set title "Throughput evolution at UDP convergence (2.31Mbps),\n 10Mbps bw, 7ms delay, 0% loss rate"
set style data linespoint

set grid
set key outside

plot "plot_udp_clean.txt" using 1:2 with lines title "UDP Throughput",\
"plot_tcp_clean.txt" using 1:2 with lines title "TCP Throughput"

