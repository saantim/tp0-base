#!/bin/bash

success="action: test_echo_server | result: success"
failure="action: test_echo_server | result: fail"
msg="testing_server"
response=$(docker run --network=tp0_testing_net busybox /bin/sh -c "echo $msg | nc server 12345")

if [ "$response" = "$msg" ]; then
  echo $success
else
  echo $failure
fi