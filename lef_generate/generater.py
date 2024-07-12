import klayout.db as db
from lef_writer import *
from typing import Any, Dict, List, Tuple, Set, Union
import os
def mydeepcopy(rg:db.Region):
    new_rg = db.Region()
    for _ in rg.each():
        new_rg.insert(_)    
    return new_rg


#读取GDS文件
def lef_generate(unit:float,gds_file:str,out_file:str,pattern:int):
    """
    This function is used to generate lef files from gds files.
    gds_file is the address of the gds file used to generate the lef file
    out_file is the address of the generated file
    unit is the association between the database and MICRONS
    """
    for root,dirs,files in os.walk(gds_file):
        for file in files:
            ly = db.Layout()
            zzw=gds_file+file
            ly.read(zzw)
            cells = ly.top_cells()
            for cell in cells:
                #从m1层提取pin信息
                M1_layer=ly.layer(19,0)  
                M1pin_layer=ly.layer(19,251)

                #从m2中提取pin信息
                M2_layer=ly.layer(20,0)  
                M2pin_layer=ly.layer(20,251)  

                #从pselect中提取site信息
                Pselect=ly.layer(13,0)
                Pselect_shapes=cell.shapes(Pselect)
                size_point=db.Point()
                for shape4 in Pselect_shapes.each():
                    if shape4.box_dp2>size_point :
                        size_point=shape4.box_dp2
                size=lef.SIZE(size_point)

                #从v1中提取通孔信息
                V1_layer=ly.layer(21,0)

                #把M1层的图形插入到region，并merge
                M1shapes = cell.shapes(M1_layer)
                r1 = db.Region()
                r1.insert(M1shapes)
                r1.merge()



                #把M2层的图形插入到region，并merge
                M2shapes = cell.shapes(M2_layer)
                r2 = db.Region()
                r2.insert(M2shapes)
                r2.merge()

                V1shapes=cell.shapes(V1_layer)
                r3 = db.Region()
                r3.insert(V1shapes)
                r3.merge()

                #遍历M1pin_layer的pin，寻找每个pin对应到M1的polygon
                M1pin_shapes = cell.shapes(M1pin_layer)
                pin_geometries={}
                obs_geometries=[]
                resm1pin = db.Region()  #收集所有用过的m1区域。从而方便分辨obs
                resm2pin = db.Region()
                resv1pin = db.Region()

                for text1 in M1pin_shapes.each():
                    bb = db.Box(text1.bbox()).center() #shape的中心点位置
                    bbox = db.Box(bb.x-1,bb.y-1,bb.x+1,bb.y+1) #以shape中心点构建的box
                    r1pin = db.Region(bbox)
                    r_c = mydeepcopy(r1)
                    res = r_c.interacting(r1pin)  #m1与pin的相交区域
                    resm1pin.insert(res)                                                      #xiugai
                    text2=text1.text
                    text3=text2.string
                    pin_geometries[text3]=[(('M1',res))]  #没有v1及m2层的情况
                    zz=r3.interacting(res) #用于检测目前循环的pin信息对应的m1是否有链接情况,zz是有pintext的m1区域与v1相交的v1区域
                    if  (r3.count!=0) and not zz.count()==0:  #有v1和m2层，找到m1通过m2层相连的m1层
                        res2_v=r2.interacting(zz) #m2层与resv_1区域相交的m2区域
                        res2_v1=r3.interacting(res2_v) #res2_v1是所有通孔与作为桥梁m2的相交区域
                        res_v1=res2_v1.not_interacting(zz) #作为一对链接通孔的另一只
                        res_m1=r1.interacting(res_v1)  #没有标记pin信息的m1区域
                        res.insert(res_m1)
                        resm1pin.insert(res_m1)
                        resm2pin.insert(res2_v) 
                        resv1pin.insert(res2_v1) 
                        pin_geometries[text3]=[(('M1',res))]

                        pin_geometries[text3].append((('M2',res2_v)))
                        pin_geometries[text3].append((('V1',res2_v1)))


                if(r2.count!=0):
                    M2pin_shapes = cell.shapes(M2pin_layer)

                    for textm2 in M2pin_shapes.each(): #筛选m2层与pin信息相交的区域
                        bb2 = db.Box(textm2.bbox()).center() #shape的中心点位置
                        bbox2 = db.Box(bb2.x-1,bb2.y-1,bb2.x+1,bb2.y+1) #以shape中心点构建的box
                        r2pin = db.Region(bbox2)
                        r_c2 = mydeepcopy(r2)
                        res2 = r_c2.interacting(r2pin)  #m2与pin的相交区域
                        textm22=textm2.text
                        textm23=textm22.string
                        pin_geometries[textm23]=[(('M2',res2))] 
                        resv1_m2=r3.interacting(res2) #与res2相交的通孔
                        resm1_v1=r1.interacting(resv1_m2) #与上述通孔相交的m1区域
                        pin_geometries[textm23].append((('M1',resm1_v1))) 
                        pin_geometries[textm23].append((('V1',resv1_m2)))
                        resm1pin.insert(resm1_v1)
                        resm2pin.insert(res2)
                        resv1pin.insert(resv1_m2)
                res_obs1=r1.not_interacting(resm1pin)
                res_obs2=r2.not_interacting(resm2pin)
                res_obs3=r3.not_interacting(resv1pin)
                if res_obs1.count()!=0:
                    obs_geometries.append(('M1',res_obs1))

                if res_obs2.count()!=0:
                    obs_geometries.append(('M2',res_obs2))

                if res_obs3.count()!=0:
                    obs_geometries.append(('V1',res_obs3))

                db_unit=unit
                scaling_factor = db_unit / (ly.dbu)
                a = 16
                scaling_factor /= a
                use_rectangles_only=True

                lef_macro = generate_lef_macro(cell.name,
                                                size=size,
                                                pin_geometries=pin_geometries,
                                                obs_geometries=obs_geometries,
                                                pin_use=None,
                                                pin_direction=None,
                                                site="asap7sc7p5t",
                                                scaling_factor=scaling_factor,
                                                use_rectangles_only=use_rectangles_only)


                # Write LEF
                output_dir=out_file
                lef_file_name = "{}.lef".format(cell.name)
                lef_output_path = os.path.join(output_dir, lef_file_name)

                if pattern==0:
                    with open(lef_output_path, "w") as f:
                        f.write(lef.lef_format(lef_macro))
                else:
                    lef_file_name = "{}.lef".format("asap7sc7p5t_28_L_1x_220121a")
                    lef_output_path = os.path.join(output_dir, lef_file_name)
                    with open(lef_output_path, "a") as f:
                        f.write(lef.lef_format(lef_macro))







    








