#!/usr/bin/python
#
# Copyright (C) 2015 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

import os
import sys
from time import sleep
import pytest
import subprocess
from halonvsi.docker import *
from halonvsi.halon import *

class PlatformSystemTests( HalonTest ):
    uuid = ""

    def setupNet(self):
        # if you override this function, make sure to
        # either pass getNodeOpts() into hopts/sopts of the topology that
        # you build or into addHost/addSwitch calls
        self.net = Mininet(topo=SingleSwitchTopo(k=0, hopts=self.getHostOpts(),
                                                 sopts=self.getSwitchOpts()),
                           switch=HalonSwitch, host=HalonHost,
                           link=HalonLink, controller=None,
                           build=True)

    def initSystemTable(self):
        # Add dummy data for LED in subsystem and led table for simulation.
        # Assume there would be only one entry in subsystem table
        s1 = self.net.switches[ 0 ]
        out = s1.cmd("ovs-vsctl list subsystem")
        lines = out.split('\n')
        for line in lines:
            if "_uuid" in line:
                _id = line.split(':')
                PlatformSystemTests.uuid = _id[1].strip()
                s1.cmd("ovs-vsctl -- set Subsystem "+PlatformSystemTests.uuid+" leds=@led1 -- --id=@led1 create led "
                "id=Led_base state=flashing status=ok")
                s1.cmd("ovs-vsctl -- set Subsystem "+PlatformSystemTests.uuid+" fans=@fan1 -- --id=@fan1 create fan "
                "name=Fan_base speed=normal direction=f2b rpm=9000 status=ok")
                s1.cmd("ovs-vsctl -- set Subsystem "+PlatformSystemTests.uuid+" power_supplies=@psu1 -- --id=@psu1 create Power_supply "
                "name=Psu_base status=ok")
                s1.cmd("ovs-vsctl -- set Subsystem "+PlatformSystemTests.uuid+" temp_sensors=@tmp1 -- --id=@tmp1 create Temp_sensor "
                "name=Temp_base location=Chassis temperature=20000 status=normal fan_state=normal")


    def deinitSystemTable(self):
        s1 = self.net.switches[ 0 ]
        # Delete dummy data from subsystem and led table to avoid clash with other CT scripts.
        s1.cmd("ovs-vsctl clear subsystem "+PlatformSystemTests.uuid+" leds")
        s1.cmd("ovs-vsctl clear subsystem "+PlatformSystemTests.uuid+" power_supplies")
        s1.cmd("ovs-vsctl clear subsystem "+PlatformSystemTests.uuid+" temp_sensors")
        s1.cmd("ovs-vsctl clear subsystem "+PlatformSystemTests.uuid+" fans")


    def showSystemTest(self):
        # Test to verify show system command
        s1 = self.net.switches[ 0 ]
        counter = 0
        print('\n==============================================================')
        print('*** Test to verify \'show system\' command ***')
        print('================================================================')
        out = s1.cmdCLI("show system")
        lines = out.split('\n')
        for line in lines:
            if 'openHalon Version' in line:
                counter += 1

            if 'Manufacturer' in line:
                if "HP Enterprise" in line:
                    counter += 1
                elif "Accton" in line:
                    counter += 1

            if 'Interface Count' in line:
                if '70' in line[:-32]:
                    counter += 1

            if 'Max Interface Speed' in line:
                if '40000' in line[42:]:
                    counter += 1

            if 'Led_base' in line:
                counter += 1

            if 'Fan_base' in line:
                counter += 1

            if 'Psu_base' in line:
                counter += 1

            if 'Temp_base' in line:
                counter += 1

        if counter == 8:
            return True

        return False



class Test_sys:
    test = PlatformSystemTests()

    def setup(self):
        pass

    def teardown(self):
        pass

    def setup_class(cls):
        # Initialize the led table with dummy value
        Test_sys.test.initSystemTable()

    def teardown_class(cls):
        # Delete Dummy data to avoid clash with other test scripts
        Test_sys.test.deinitSystemTable()
        # Stop the Docker containers, and
        # mininet topology
        Test_sys.test.net.stop()

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    def __del__(self):
        del self.test

    # show system test.
    def test_show_system_command(self):
       if self.test.showSystemTest():
           print 'Passed System Test'
       else:
           assert 0, "Failed System Test"
