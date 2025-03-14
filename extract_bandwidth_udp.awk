#!/usr/bin/awk -f

/^\[ *[0-9]+\]/ {
	split($3, interval, "-");
	time = interval[2];
	bandwidth = $(NF-6);
	unit = $(NF-5);

	if (unit == "Kbits/sec"){
		bandwidth = bandwidth / 1000;
	}

	print time, bandwidth;
}
