#!/bin/bash

PID=$(ps aux | grep contingent | grep -v grep | awk {'print $2'} | tr " " "\n")

for i in $PID
do
	kill $i
done
