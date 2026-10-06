# 0-直接使用MLP生成权重作为滤波器
# 1-改进滤波器(趋势+均值)
# 1_1-改进滤波器(均值)
# 1_2-改进滤波器(趋势)
# 2-改进滤波器(滑动窗口+趋势+均值)
# 2_1-改进滤波器(滑动窗口+均值)
# 2_2-改进滤波器(滑动窗口+趋势)
# 3-多专家动态卷积
# 4-空洞卷积
# 5-SE卷积
# 6-分组卷积
# 7-深度可分离卷积
# 8-原始卷积网络

# 保存模型序号
Model_id = "1"

sample_id = 10
# 保存结果图路径,编号num1,这里4/2，3/1
num1 = 5
num = 1
folder_path = "../figure"+str(num1)+"/"+str(Model_id)+"_figure"

# 最佳组合1,256,8,32,0.003
In_channels = 1  # 这个参数不优化, 随着输入维度变化而变化，比如不加入物理领域知识，维度设置为1
Conv_channels = 256
Cbam_reduction = 16
Batch_size = 32
Learn_rate = 0.003
num_epochs = 50
dropout = 0.4

window_size = 5

# CNN参数，原始3、1、1，为了保持尺寸不变
# 组合：1、0；
# 3、1；
# 5、2；
# 7、3
kernel_size = 3
padding = 1  # (kernel_size - 1) // 2

# 可视化层
layer1 = ["concat"+str(num)+""]
layer2_1 = "ca_weight"+str(num)+""
# layer2_2 = "sa_weight"+str(num)+""
layer2_3 = "simam"+str(num)+""
