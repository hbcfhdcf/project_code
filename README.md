创立一个名为gds和一个名为output_lef的文件夹，其中gds中放入要生成lef文件所需要的gds文件，output_lef文件夹存放输出的lef文件
本代码提供格式的输出选项，在lef_generate函数中的第四个参数为一个整数，填0则每一个cell输出一个文件，填1则将所有cell输入到同一个文件中
本代码仅适用于asap7代码，若想适用于其他工艺库，则需要修改layer层的信息，例如：在asap7工艺中m1层是（19,0），所以代码提取m1层用的就是klayout中的layout.layer（19,0）
要使用本代码需要下载klayout的python库
