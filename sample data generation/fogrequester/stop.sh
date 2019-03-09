#!/bin/bash
ps -ef | grep "fog-requester.jar" | awk '{print $2}' | xargs kill

