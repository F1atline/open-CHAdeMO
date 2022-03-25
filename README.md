# open-CHAdeMO
## What is it?

It's a open source software for realization CHAdeMO standard: [2030.1.1-2015 - IEEE Standard Technical Specifications of a DC Quick Charger for Use with Electric Vehicles](https://ieeexplore.ieee.org/document/7400449) \
Platform: Windows, macOS, Linux.

## Terms

## CAN Messages

<table>
    <thead>
        <tr>
            <th>Source</th>
            <th>Destination</th>
            <th>ID</th>
            <th>Byte</th>
            <th>Contetnt</th>
            <th>Remarks</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan=24>Vehicle</td>
            <td rowspan=24>Charger</td>
            <td rowspan=8>0x100</td>
            <td>0</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td>1</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td>2</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td>3</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td>4</td>
            <td>Maximum battery voltage, 1V / bit, 0 V to 600 V</td>
            <td>Low byte</td>
        </tr>
        <tr>
            <td>5</td>
            <td>Maximum battery voltage, 1V / bit, 0 V to 600 V</td>
            <td>Hight byte</td>
        </tr>
        <tr>
            <td>6</td>
            <td>Charged rate reference constant, 1% / bit, max 100%</td>
            <td>for display</td>
        </tr>
        <tr>
            <td>7</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td rowspan=8>0x101</td>
            <td>0</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td>1</td>
            <td>Maximum charging time, 10 s / bit, 0 s to 2540 s, “0xFF” indicates usage of Byte 2 (by minute)</td>
            <td>by 10 second</td>
        </tr>
        <tr>
            <td>2</td>
            <td>Maximum charging time, 1 min / bit, 0 to 255 min</td>
            <td>by minute</td>
        </tr>
        <tr>
            <td>3</td>
            <td>Estimated charging time, 1 min / bit, offset 1, 0 min to 254 min</td>
            <td>by minute</td>
        </tr>
        <tr>
            <td>4</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td>5</td>
            <td>Total capacity of battery (Declared value). Option. 0.1 kWh / bit, 0.0–6553.5 kWh</td>
            <td>Low byte</td>
        </tr>
        <tr>
            <td>6</td>
            <td>Total capacity of battery (Declared value). Option. 0.1 kWh / bit, 0.0–6553.5 kWh</td>
            <td>Hight byte</td>
        </tr>
        <tr>
            <td>7</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td rowspan=8>0x102</td>
            <td>0</td>
            <td>CHAdeMO control protocol number, 1 / bit, Ver. 0 to 255</td>
            <td></td>
        </tr>
        <tr>
            <td>1</td>
            <td>Target battery voltage, 1 V / bit, 0 V to 600 V</td>
            <td>Low byte</td>
        </tr>
        <tr>
            <td>2</td>
            <td>Target battery voltage, 1 V / bit, 0 V to 600 V</td>
            <td>High byte</td>
        </tr>
        <tr>
            <td>3</td>
            <td>Charging current request, 1 A / bit, 0 A to 255 A</td>
            <td></td>
        </tr>
        <tr>
            <td>4</td>
            <td>Fault flag</td>
            <td><a href="#102_fault">see a description after the table</a></td>
        </tr>
        <tr>
            <td>5</td>
            <td>Status flag</td>
            <td><a href="#102_status">see a description after the table</a></td>
        </tr>
        <tr>
            <td>6</td>
            <td>Charged rate, 1% / bit, 0% to 100%</td>
            <td>for display</td>
        </tr>
        <tr>
            <td>7</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td rowspan=16>Vehicle</td>
            <td rowspan=16>Charger</td>
            <td rowspan=8>0x108</td>
            <td>0</td>
            <td>Identifier of support for EV contactor welding detection, 1 / bit, Ver. 0 to 255</td>
            <td>0: Not supporting EV</td>
        </tr>
        <tr>
            <td>1</td>
            <td>Available output voltage, 1 V / bit, 0 V to 600 V</td>
            <td></td>
        </tr>
        <tr>
            <td>2</td>
            <td>Available output voltage, 1 V / bit, 0 V to 600 V</td>
            <td></td>
        </tr>
        <tr>
            <td>3</td>
            <td>Available output current, 1 A / bit, 0 A to 255 A</td>
            <td></td>
        </tr>
        <tr>
            <td>4</td>
            <td>Threshold voltage, 1 V / bit, 0 V to 600 V</td>
            <td></td>
        </tr>
        <tr>
            <td>5</td>
            <td>Threshold voltage, 1 / bit, Ver. 0 to 255</td>
            <td></td>
        </tr>
        <tr>
            <td>6</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td>7</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td rowspan=8>0x109</td>
            <td>0</td>
            <td>CHAdeMO control protocol number, 1 / bit, Ver. 0 to 255</td>
            <td></td>
        </tr>
        <tr>
            <td>1</td>
            <td>Present output voltage, 1 V / bit, 0 V to 600 V</td>
            <td></td>
        </tr>
        <tr>
            <td>2</td>
            <td>Present output voltage, 1 V / bit, 0 V to 600 V</td>
            <td></td>
        </tr>
        <tr>
            <td>3</td>
            <td>Present charging current, 1 A / bit, 0 A to 255 A</td>
            <td></td>
        </tr>
        <tr>
            <td>4</td>
            <td></td>
            <td>Reserved</td>
        </tr>
        <tr>
            <td>5</td>
            <td>Status / fault flag</td>
            <td><a href="#109_status">see a description after the table</a></td>
        </tr>
        <tr>
            <td>6</td>
            <td>Remaining charging time, 10 s / bit, 0 s to 2540 s, “0xFF” indicates usage of Byte 2 (by minute)</td>
            <td>by 10 second</td>
        </tr>
        <tr>
            <td>7</td>
            <td>Remaining charging time, 1 min / bit, 0 min to 255 min</td>
            <td>by minute</td>
        </tr>
    </tbody>
</table>

### <a id="102_fault"></a>Description fault flag (vehicle) ID:0x102

<table>
    <thead>
        <tr>
            <th>Byte</th>
            <th>Max</th>
            <th>Bit</th>
            <th>Description</th>
            <th>Value</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan=8 align="center">4</td>
            <td rowspan=4 align="center">1</td>
            <td>0</td>
            <td>Battery overvoltage</td>
            <td>0: normal, 1: fault</td>
        </tr>
        <tr>
            <td>1</td>
            <td>Battery under voltage</td>
            <td>0: normal, 1: fault</td>
        </tr>
        <tr>
            <td>2</td>
            <td>Battery current deviation error</td>
            <td>0: normal, 1: fault</td>
        </tr>
        <tr>
            <td>3</td>
            <td>High battery temperature</td>
            <td>0: normal, 1: fault</td>
        </tr>
        <tr>
            <td rowspan=4 align="center">F</td>
            <td>4</td>
            <td>Battery voltage deviation error</td>
            <td>0: normal, 1: fault</td>
        </tr>
        <tr>
            <td>5</td>
            <td>Reserved</td>
            <td>0: always</td>
        </tr>
        <tr>
            <td>6</td>
            <td>Reserved</td>
            <td>0: always</td>
        </tr>
        <tr>
            <td>7</td>
            <td>Reserved</td>
            <td>0: always</td>
        </tr>
    </tbody>
</table>

### <a id="102_status"></a>Description status flag (vehicle) ID:0x102

<table>
    <thead>
        <tr>
            <th>Byte</th>
            <th>Max</th>
            <th>Bit</th>
            <th>Description</th>
            <th>Value</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan=8 align="center">5</td>
            <td rowspan=4 align="center">1</td>
            <td>0</td>
            <td>Vehicle charging enabled</td>
            <td>0: disabled,<br> 1: enabled</td>
        </tr>
        <tr>
            <td>1</td>
            <td>Vehicle shift position</td>
            <td>0: “Parking” position,<br> 1: other position</td>
        </tr>
        <tr>
            <td>2</td>
            <td>Charging system fault</td>
            <td>0: normal,<br> 1: fault</td>
        </tr>
        <tr>
            <td>3</td>
            <td>Vehicle status</td>
            <td>0: EV contactor close or during welding detection,<br> 1: EV contactor open or termination of welding detection</td>
        </tr>
        <tr>
            <td rowspan=4 align="center">F</td>
            <td>4</td>
            <td>Normal stop request before charging</td>
            <td>0: No request,<br> 1: Stop request</td>
        </tr>
        <tr>
            <td>5</td>
            <td>Reserved</td>
            <td>0: always</td>
        </tr>
        <tr>
            <td>6</td>
            <td>Reserved</td>
            <td>0: always</td>
        </tr>
        <tr>
            <td>7</td>
            <td>Reserved</td>
            <td>0: always</td>
        </tr>
    </tbody>
</table>

### <a id="109_status"></a>Description status / fault flag (charger), ID: 0x109

<table>
    <thead>
        <tr>
            <th>Byte</th>
            <th>Max</th>
            <th>Bit</th>
            <th>Description</th>
            <th>Value</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan=8 align="center">5</td>
            <td rowspan=4 align="center">3</td>
            <td>0</td>
            <td>Charger status</td>
            <td>0: standby,<br> 1: charging</td>
        </tr>
        <tr>
            <td>1</td>
            <td>Charger malfunction</td>
            <td>0: normal,<br> 1: fault</td>
        </tr>
        <tr>
            <td>2</td>
            <td>Charging connector lock</td>
            <td>0: open,<br> 1: locked</td>
        </tr>
        <tr>
            <td>3</td>
            <td>Battery incompatibility</td>
            <td>0: compatible,<br> 1: incompatible</td>
        </tr>
        <tr>
            <td rowspan=4 align="center">F</td>
            <td>4</td>
            <td>Charging system malfunction</td>
            <td>0: normal,<br> 1: malfunction</td>
        </tr>
        <tr>
            <td>5</td>
            <td>Charging stop control</td>
            <td>0: operating,<br> 1: stopped or stop charging</td>
        </tr>
        <tr>
            <td>6</td>
            <td>Reserved</td>
            <td>0: always</td>
        </tr>
        <tr>
            <td>7</td>
            <td>Reserved</td>
            <td>0: always</td>
        </tr>
    </tbody>
</table>
