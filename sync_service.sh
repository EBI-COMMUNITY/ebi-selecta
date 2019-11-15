#!/bin/sh


sh -c 'for service in service_*; do echo $service; cp -rv fig LICENSE requirements.txt resources docs README.md scripts db submission $service/ ; done'
