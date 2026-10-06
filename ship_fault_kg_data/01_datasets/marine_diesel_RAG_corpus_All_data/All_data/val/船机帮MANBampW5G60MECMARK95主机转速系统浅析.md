# 导读

主机转速系统对于主机的运行特别重要，它是主机控制系统的重要部件之一，如果发生故障，影响主机正常运行，严重时会导致瘫船，所以机舱管理人员一定要对其组成，性能特点熟练掌握，以利遇到问题时，能够不慌不忙，果断解决，现将DMD MAN B&W 5G60ME-C9.5+LPSCR(Tier III) 主机转速系统（Tacho System）的组成，角度编码器调整方法，MOP转速系统功能试验，TDC标定方法及常见报警项目描述出来，供同行参考和探讨。

## 一、主机主要常数

概述（Description）：二冲程，单作用，直连螺旋桨可以逆转十字头型船用柴油机型号(Type): DMD-MAN B&W 5G60ME-C Mark 9.5 + LPSCR (Tier III)

缸数(Number of Cylinder): 5

缸径(Cylinder Bore)：600MM

活塞冲程(Piston Stroke)：2790MM

最大服务功率（SMCR）: 8304KW @97RPM

持续服务功率（CSR）: 6120 @71.8RPM (73.7%SMCR)

MEP@SMCR平均有效压力：15.9 BAR

P-Max @SMCR爆发压力：171 BAR

SFOC@CSR油耗：155.9 g/kwh + 6%(Tier II),157 g/kwh + 6%(Tier III)

旋转方向（Rotation）（从船尾看）：顺时针

发火顺序(Firing Order)：1-4-3-2-5

增压器(Turbocharger)：TCA55-21 X 1台

电制(Power Supply)：AC 3X440V / 60Hz, AC 1X220V / 60Hz, DC24V

厂家(Maker)：中国船舶重工集团大连船舶柴油机有限公司

## 二、转速系统

### （Tacho System）的概述

MAN B&W 5G60ME-C9.5 主机转速系统是由两套互为冗余的角度编码系统A和B，气缸控制单元（CCU）和主机控制单元（ECU）组成，角度编码系统提供燃油喷射定时，气缸油注油定时，排气阀开启关闭定时。

图1

图2

图3

它们分别由编码器（Angle Encoder A, Angle Encoder B）（如图1所示），, 编码器信号放大器（TSA-A, TSA-B）（如图2所示）和MSA探头（如图3所示）组成，编码器（Angle Encoder A, Angle Encoder B）安装在主机自由端（前侧）， 前面的一组叫编码器B(Angle Encoder B),它的基准定时标记角度为1缸上死点后450，后面的一组叫编码器A(Angle Encoder A), 它的基准定时标记角度1缸上死点00，还有一只MSA探头和导磁标记环（Marker Ring），它的基准定时标记角度为1缸上死点后900，起参考（Reference Sensor）作用，属于角度编码系统A，角度编解码系统A内的MSA探头没有使用（如下图4所示），MSA探头安装在主机输出端（飞轮侧）,角度编码系统A和B是互为备用的，如果系统A或B失效，主机仍可正常运行，只不过MOP 界面会出现报警，但是如果两组系统A和B同时失效, 主机将会停车或不能启动；

如果角度编码器换新，那必须调整它的定时基准角度和进行MOP界面转速系统的功能试验（Function Test），以确保其工况正常。

以下为各种缩写字母的解释：

TSA: Tacho Set A 转速系统A

TSB: Tacho Set B转速系统B

TSA-A: Tacho Set A Amplifier转速系统A信号放大器

TSB-A: Tacho Set B Amplifier 转速系统B信号放大器

MMA : Marker Master A 主标记A

MMB: Marker Master B主标记B

MSA: Marker Slave A 副标记A

MSB: Marker Slave B副标记B

ECU: Engine Control Unit 主机控制单元

CCU: Cylinder Control Unit 气缸控制单元

TDC: Top Dead Center 上死点

MOP: Main Operation Panel 主操作站

PMI: Pressure Measurement Instrument 压力测量仪器

LED: Light Emit Diode 发光二极管

MPC: Multi – Purpose Controller 多功能控制板

PCB: Printed Circuit Board 印刷电路板

CSR: Continuous Service Rating 持续服务功率

SMCR: Maximum Service Continuous Rating 最大持续服务功率

SFOC: Specific Fuel Oil Consumption 特定的燃油消耗率

Pmax: 最大爆压，Pcom: 压缩压力，Pi: 指示压力

## 三、转速系统各部件工作示意图如下

图4

TSA系统 (电源来自于ECUA)

MMA = Marker Master A

MSA = Marker Slave A

Q1A = Quadrature 1A

Q2A = Quadrature 2A

TSB系统(电源来自于ECUB)

MMB = Marker Master B

MSB = Marker Slave B

Q1B = Quadrature 1B

Q2B = Quadrature 2B

图5

通过图4，图5和列表(Table1)，我们不难理解角度编码器的基本结构和工作原理, 角度编码器A内置四个固定无触点探头MMA,MSA,Q1A,Q2A,角度编码器B内置四个固定无触点探头MMB,MSB,Q1B,Q2B,另外在飞轮侧1缸上死点后90度安装一只机械固定的MSA探头，它的接线接入角度编码器A的信号放大器接线盒内，取代了角度编码器A上内置的MSA探头，就是说角度编码器A上的内置MSA探头没有使用，角度编码器B的内置四个探头均接入其信号放大器接线盒内，因此角度编码器信号放大器接线盒的接线多于角度信号放大器B接线盒接线。

现以角度编码器A为例结合图5简述其工作原理，MMA探头是标记1缸上死点位置的标记探头，MSA是起参考作用的探头，Q1A和Q2A探头探测主机转速，转向和曲柄运转的角度，角度编码器内部有一只随主机曲轴转动的带有360个齿(z)的圆盘，每转动一个齿，Q1A和Q2A探头就会感受一个脉冲信号（f），TSA-A信号放大器的计数器就记录一个数，并通过记录脉冲次数计数（脉冲频率）反映主机曲轴的转动速度（n=60f/z, n为转速，单位为r/m,f为脉冲频率，z为圆盘齿数），如果主机顺时针转动（如图4），Q2A比Q1A先感应到信号，如果主机逆时针转动（如图5），Q1A比Q2A先感应到信号，根据Q1A和Q2A感应信号的先后顺序即可判断主机的旋转方向及正倒车方向，圆盘上固定一个半圆导磁环（灰色半圆环）随圆盘一起转动，当半圆导磁环转动到MMA探头位置时，MMA探头感应到一个脉冲信号识别主机1缸上死点位置，系统根据Q1A,Q2A及MMA的信号输入计算出曲轴角度，为防止角度编码器的转动圆盘与传动轴产生滑动而影响其精确性，在主机飞轮上安装了一个固定的180度的导磁环（Marker Ring）和一只固定MSA探头，当导磁环到达MSA探头位置时，MSA就感应到一个持续180度的脉冲信号，将其与系统计算出的主机曲轴转角进行比较，即可判断角度编码器的工况是否正常。

列表中(Table1)将编码器标记位置探头MMA(B)和MSA(B)感应到信号为True(T), 感应不到信号为False(F),在MOP界面进行Tacho Function Test时，当1缸在上死点（TDC1）0度时，界面出现A:TF B:FF 的意思就不难理解了，此时，MMA: True，MSA: False, MMB: False, MSB: False (如下图7所示)。

## 四、角度编码器的调整方法

### 1、调整前准备：

确认编码器接线正确，解码器已供电，主机盘车机合上，主机各缸示功阀已打开，在主机自由端有2只编码器信号放大器接线盒（如图2），一只为TSA-A, 另一只为TSB-A, TSA-A接线盒的接线来自编码器A 和MSA探头，而TSB-A的接线来自编码器B(如图4所示)，两只编码器的定时基准角度调整方法是一样的，只不过TSA编码器的基准定时曲柄角度为1缸上死点0度，TSB编码器的基准定时曲柄角度为1缸上死点后45度（如图3所示）。

### 2、调整方法：

将主机进行盘车，直至编码器放大器接线盒上的LED(发光二极管)指示灯变亮时(如图6所示)，停止盘车，查看此时飞轮上的角度，对于TSA来说，应该是0-0.5度，如果飞轮上的刻度是0-0.5度时，TSA放大器接线盒上的LED不亮，说明TSA编码器安装不对，需调整，松开TSA解码器上的锁紧螺丝（3MM内六角螺丝），转动TSA编码器，直到编码器放大器接线盒上的LED指示灯变亮，锁紧编码器上的锁紧螺丝，此时调整结束，再盘车一圈，当飞轮上指针刻度在0-180度时，检查确认TSA放大器接线盒上LED指示灯一直是常亮状态，对于飞轮处MSA探头的调整，先检查MSA探头与触发环（Marker Ring）的间隙是否为1.5MM – 3.0MM, 如果间隙正确，盘车至1缸上死点90度，检查TSA-A接线盒上的LED指示灯是否变亮，如果不亮，检查接线是否正确，MSA探头是否损坏，逐一排查。TSB角度编码器的调整是盘车至1缸上死点后45度时，TSB-A放大器接线盒上LED指示灯变亮。

图6

## 五、MOP界面转速系统的功能试验

### 1、准备工作：

在MOP界面，点击System Option Operator后出现对话框，点击Chief Level 输入密码BADOIT, 点击Enter, Mop界面右下方出现Chief 图标，一人拿着对讲机在主机飞轮旁用盘车机进行盘车，另一人拿着对讲机在主机MOP人机界面旁，并发出相应的盘车角度指令（3580,2，470，920,1370）给飞轮侧人员，打开主机各缸示功阀，合上盘车机。

图7

### 2、功能试验（如图7所示）：

在MOP界面点Maintenance >>> 点Function Test >>>点Tacho>>>点Start>>>盘车至1缸上死点前20 （飞轮358度刻度指针）>>> Reboot CCUs和ECUs>>>20 >>>470>>>920>>>1370当飞轮刻度指针逐次达到上述角度时，MOP界面Test Value 栏目下方相应行的背景颜色由黄色变为灰色，同时，MOP人机界面旁的人员点击MOP界面下方的DONE按钮，Test Value 栏目下方相应行显示OK后进行下一步，如果不能按上述步骤一步一步进行下去，那么是角度编码器或MSA探头或者是接线存在问题，需进一步检查。

### 3、角度编码器参数的细调

细调的前提条件：

主机运行在50%负荷左右，使用MOP人机界面Auto Tuning 使各个气缸热工参数（Pmax, Pcom, Pi）基本均衡，完成TDC标定试验；

图8

TDC标定试验（如图8所示），进入PMI电脑人机界面，点击Maintenance>>>点击Tool>>>进入Performance TDC Calibration 界面后点击Run Wizard,点击Automatic>>>点击Next>>>等待5-10分钟，TDC标定试验完成后，各缸的TDC值及Trig A Offset Ahead 值将自动存储，如下图9所示；

图9

点击OPEN查看各缸TDC数值和Trig A Offset Ahead 数值，标定后的“Trig A Offset Ahead”值可在主机停止后通过轮机长权限输入至Tacho Alignment Deviation 栏目中（如图7）。

## 六、转速系统的几种故障及处理

### 1、Tacho Set A Failure (转速系统A失效)

MOP界面报警显示转速系统A信号异常；

转速系统A（TSA）失效的原因：

A. 如果是飞轮侧MSA探头失效，所有的CCU和ECU将会出现转速系统A失效，新的MSA探头必须安装更换，飞轮侧MSA探头失效属于高发故障，可以从MOP界面Maintenance>>>Function Test >>>Tacho>>>Test Detail 界面查看判断，如果手头没有MSA探头备件，可以利用下述方法暂时将报警消除，由于TSA-A内MSA探头没有使用，可用TSA-A内的MSA探头接线替代飞轮侧的MSA探头接线，一般情况下，TSA-A信号放大器接线盒内有一只连接TSA内部MSA探头接线的备用插头（Plug），这样可以把连接飞轮侧MSA探头的插头（Plug）拔掉，用TSA-A内的MSA探头接线的插头（Plug）插上即可，如下图10-11所示。

图10

图11

B. 角度编码器A失效；

C. 接线松脱；

D. TSA-A放大器PCB板失效；

E. CCU失效（MPC-10），可以从MOP界面Maintenance>>>Function Test >>> Tacho>>>Test Detail 界面查看判断哪一个CCU失效；

F. 电源失效（TSA 连接ECUA电源，TSB 连接ECUB电源）；

建议采取措施：

如果仅一只CCU失效，检查失效的CCU上的接头 J40 – J43, 如果接头正常，那么这个CCU必须换新;

如果是所有CCU和ECU显示Tacho Set A 失效，在MOP Maintenance System I/O Test界面检查编码器输入信号：

盘车机盘车至少1转，在失效的CCU 界面上检查通道40-43是否在True(T)和False(F)之间正确显示，通道40+41每转一转显示T和F两次, 通道42+43每转一转显示T和F多次，在MOP界面根据Tacho Test 步骤进行Maintenance>>>Function Test >>> Tacho>>>Test Detail结合MOP Maintenance System I/O Test界面查找出故障来自于以下哪个部件(1) 编码器和（或者）飞轮侧探头，(2)放大器板（TSA-A）(3) ECUA（如图12-13所示）。

图12

图13

### 2、Tacho Set B (TSB)失效

转速系统B失效的原因和转速系统A差不多，只不过转速系统B没有飞轮侧MSB探头失效这一故障，它是利用TSB编码器内部的MSB探头，这里不再描述。

### 3、转速系统B变量太大（Delta Tacho Set B too Big）

MOP界面显示Delta Tacho Set B too Big警报，两套转速系统的对中不在允许差值内（-1.00 – 1.00），这种报警在两套系统（TSA和TSB）都没有失效的情况下才会发生的，如果出现上述报警，可根据需要检查Pmax，如有必要进行Pmax调整，这种报警不影响主机正常运行，在主机停用时，检查和调整纠正角度编码器的基准定时曲轴角度，以消除该报警。

### 4、转速对中误差（Tacho Alignment Error）

MOP界面显示Tacho Alignment Error,一套或两套转速超出调节范围，主要原因是编码器位置滑移或者是解码器探头安装不正确，由于微小的发火定时，单缸爆压可能改变，如果叠加其它因素，可能使TSA转到TSB或由TSB转到TSA, 这种报警在两套系统（TSA和TSB）都没有失效的情况下才会发生的，如果出现上述报警，可根据需要检查Pmax，如有必要进行Pmax调整，这种报警不影响主机正常运行。

Tacho Alignment Deviation 过大时才会出现Tacho Alignment Error警报，通常情况下，Tacho Alignment Deviation数值为0，这个警报可用以下方法消除，通过PMI计算机进行TDC标定，完成TDC标定之后，查看Trig A Offset Ahead的数值，将此数值在主机停用时用轮机长权限输入到主机MOP界面的Tacho A Alignment Deviation 栏目中即可（如下图14所示），在主机停用时，检查和调整纠正角度编码器的基准定时曲轴角度，以消除该报警。

图14

## 七、结束语

通过上述主机转速探头的相关浅析，我们发现一个重要现象，随着科技的进步，船舶机电设备的自动化，智能化程度越来越高，轮机管理人员不仅要懂得机电设备的知识，也要懂电脑软件方面的知识，这就要求我们在工作中不断学习总结，探讨研究说明书，与时俱进，不断提高自己的业务技能，这样才能在工作中得心应手，游刃有余。