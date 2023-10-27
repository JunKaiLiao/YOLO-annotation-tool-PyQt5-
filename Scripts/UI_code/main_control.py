from UI_0329 import Ui_MainWindow
from PyQt5.QtWidgets import QFileDialog 
import sys
import json
import numpy as np
import shutil
import datetime
from PyQt5.QtGui import QPixmap, QImage, QPen, QPainter
from PyQt5.QtCore import QRect, Qt
import cv2
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox
import os
from qt_material import apply_stylesheet

class MainWindow_controller(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__() 
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)  #call ui

        # initial value
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.drag = True
        self.content= [] # put new annotation
        self.show_GUI=[] # put new annotation that will be showed on GUI
        self.enter_x=[];self.enter_y=[];self.enter_label=[]
        self.add_label=''
        self.class_dic = {0:'G', 1:'R', 2:'Y'}
        self.class_dic_reverse = {'G':0, 'R':1, 'Y':2}
        self.color_dict = {'G':(0, 255, 0), 'R':(0, 0, 255), 'Y':(0, 128, 255)}
        self.setup_control()

    def setup_control(self):
        self.ui.push_select_img.clicked.connect(self.open_img_folder)
        self.ui.push_select_Json.clicked.connect(self.open_Json_file)
        self.ui.push_reset.clicked.connect(self.reset)
        self.ui.push_add.clicked.connect(self.add)
        self.ui.push_save.clicked.connect(self.save)
        self.ui.file_list.clicked.connect(self.filename_clicked)
        self.ui.txt_list.clicked.connect(self.delete_ANN)
        self.ui.push_save_polygon.clicked.connect(self.enter_save_polygon)
        self.ui.push_delete_polygon.clicked.connect(self.remove_current_polygon)
        self.ui.push_export.clicked.connect(self.export)

        # mouse event 
        self.ui.show_2.mousePressEvent = self.get_clicked_position

        # theme
        self.ui.action_dark_teal.triggered.connect(self.dark_teal)
        self.ui.action_light_teal.triggered.connect(self.light_teal)

    def open_img_folder(self):
        self.dir_path = QFileDialog.getExistingDirectory(self, "Open Image folder", "./")  #get the folder path
        if (self.dir_path == ''):            
            return
        self.list_file()
    
    def list_file(self):
        self.ui.file_list.clear(); content = []
        for imgName in os.listdir(self.dir_path):
            if os.path.isfile(os.path.join(self.dir_path, imgName)):
                content.append(imgName) 
        self.ui.file_list.addItems(content)
        
    def open_Json_file(self):
        self.JsonFile_path, filetype = QFileDialog.getOpenFileName(self, "Open Json file", "./")  
        if (self.JsonFile_path == ''):            
            return
        else:
            self.jsonFile = open(self.JsonFile_path, 'r', encoding='utf-8')  # error:沒加上utf-8會以cp590編碼
            self.JsonExist = True
            self.jsonInfo = json.load(self.jsonFile)

    def defineFilePath(self):
        self.stripFileName = self.clickedItem[:-4] # 目前點擊的檔名(去除附檔名)
        self.oringinal_image_path = os.path.join(self.dir_path, self.clickedItem)
        self.predict_ANN_path = self.dir_path.strip('Original_Image') + 'Predict_Annotation/' + self.clickedItem[:-4] + '.txt'
        self.new_ANN_folder = self.dir_path.strip('Original_Image') + '/New_Annotation'
        self.new_ANN_path = os.path.join(self.new_ANN_folder, self.clickedItem[:-4] + '.txt')
    
    def getFirstKey(self): # 提取Json資訊的第一個KEY
        imgBytes = str(os.path.getsize(os.path.join(self.oringinal_image_path))) # 取得影像位元組
        self.firstKey = self.clickedItem + imgBytes

    def filename_clicked(self): # 當點擊檔名
        self.ui.show_1.clear(); self.ui.show_2.clear(); self.content=[]
        self.clickedItem = self.ui.file_list.currentItem().text()
        self.defineFilePath(); self.getFirstKey(); self.display_ground_truth()
        self.display_annotation_info()
        self.reset_backup = self.jsonInfo[self.firstKey] # 避免按下reset後將所有更動的json資訊重置
        self.save = False # 避免未做任何操作而發生閃退

        # 若存在新標註檔，則顯示新標註檔的資訊
        if os.path.exists(self.new_ANN_path):
            draw_bbox(self.oringinal_image_path, self.new_ANN_path)
        else:
            draw_bbox(self.oringinal_image_path, self.predict_ANN_path)
        self.show2('predict.png')
    
    def display_annotation_info(self):
        self.ui.txt_list.clear()
        id = 1 ; self.write_into_txt2= []; self.ANN_show2=[]
        if os.path.exists(self.new_ANN_path):
            self.ui.txt_list.addItems(['The image has been edited. If you would like to edit, please press the reset button.'])
        else:
            if self.predict_ANN_path == '':
                print('No such file !')
            else:
                with open(self.predict_ANN_path) as f:
                    for line in f.readlines():
                        ANN_show=[];write_into_txt=[]       # 逐行讀取
                        s = line.split(' ')
                        ANN_show.append(str(id)+'.')
                        for i in range(len(s)):
                            write_into_txt.append(s[i].replace('\n', ''))  #存放待輸入進檔案裡的資料
                            if i == 0 :
                                ANN_show.append(self.class_dic[int(s[i])]) #存放將顯示於GUI上的資料
                            else:
                                ANN_show.append(s[i].replace('\n', ''))
                        id += 1
                        my_lst_str = ' '.join(map(str, ANN_show)) 
                        self.ANN_show2.append(my_lst_str)
                        write_into_txt = ' '.join(map(str, write_into_txt))
                        self.write_into_txt2.append(write_into_txt)
                    self.ui.txt_list.addItems(self.ANN_show2)

    def delete_ANN(self):
        del_index = self.ui.txt_list.currentIndex().row()
        item = self.ui.txt_list.takeItem(del_index) 
        self.ui.txt_list.removeItemWidget(item)                      # remove item on GUI
        self.write_into_txt2.remove(self.write_into_txt2[del_index]) # remove 檔案裡的 ANN
        self.save=True
        # 若再次點擊，則更新一次 (必須處理id會自動更新的問題) --> 目標：若有1 2 3 個標註，點擊2刪除後， 希望3會自動遞補為2。
        # 暫存一個txt用來存放刪除的項目 (處理顯示標註檔的問題) 
        del_file = 'del.txt'
        file = open(del_file, 'w')
        for item in list(self.write_into_txt2):
            file.write(item+'\n')
        file.close()
        self.show_del_ANN=[]; id = 1
        with open(del_file) as f:
            for line in f.readlines():
                ANN_show=[]
                s = line.split(' ')
                ANN_show.append(str(id)+'.')
                for i in range(len(s)):
                    if i == 0 :
                        ANN_show.append(class_dic[int(s[i])]) #存放將顯示於GUI上的資料
                    else:
                        ANN_show.append(s[i].replace('\n', ''))
                id += 1
                my_lst_str = ' '.join(map(str, ANN_show)) 
                self.show_del_ANN.append(my_lst_str)
                self.ui.txt_list.clear()
            self.ui.txt_list.addItems(self.show_del_ANN) # 更新目前的標註資料
        os.remove(del_file)
        self.temporary_save_txt()

    def temporary_save_txt(self):
        self.write_txt = self.write_into_txt2 + self.content   # write_txt 寫入檔案裡
        file = open('./'+ self.clickedItem[:-4] + '.txt', 'w')    # temporary save
        for item in self.write_txt:
            file.write(item+"\n")
        file.close()

        if not self.enter_x: # 若沒有新增的mask
            draw_bbox(self.oringinal_image_path, self.clickedItem[:-4] + '.txt')
        else: 
            draw_bbox('predict.png', self.clickedItem[:-4]+ '.txt')

        os.remove(self.clickedItem[:-4] + '.txt')
        self.show2('predict.png')
    
    def reset(self):
        self.content = []; self.save = False
        self.add_pos=[]; self.add_x_pos=[]; self.add_y_pos=[];self.add_line=[];self.add_circle=[]
        self.enter_x=[]; self.enter_y=[]; self.enter_label=[] # 更新儲存內容
        if os.path.exists(self.new_ANN_path):  # 已編輯過的影像，若想重新編輯，則刪除新標註檔
            os.remove(self.new_ANN_path)
        self.jsonInfo[self.firstKey] = self.reset_backup
        self.display_annotation_info()
        draw_bbox(self.oringinal_image_path, self.predict_ANN_path)
        self.show2('predict.png')

    def show2(self, img):
        self.ui.show_2.clear()
        image = cv2.imread(img)
        ori_bytesPerline = 3 * self.width
        Q = QPixmap(QImage(image, self.width, self.height, ori_bytesPerline, QImage.Format_RGB888).rgbSwapped())
        self.ui.show_2.setPixmap(Q);self.ui.show_2.setScaledContents(True); self.ui.label_show2.setText('Predict Image')
        # os.remove('predict.png')    

    def display_ground_truth(self):
        image = cv2.imread(self.oringinal_image_path)
        self.height, self.width, channel = image.shape
        num_mask = len(self.jsonInfo[self.firstKey]['regions']) # 需要畫多少個mask
        if num_mask == 0:  # 當刪除所有標註或原標註檔為負樣本，顯示原圖
            cv2.imwrite('Ground_Truth.png', image)
        else:
            if self.width > 1000 and self.width < 1200:   # 避免圖片解析度太高，導致會出來的線太細
                line_width = 3
            elif self.width >=1200 and self.width <1400:
                line_width = 4
            elif self.width >= 1400:
                line_width = 6
            else:
                line_width = 1

            for index in range(num_mask):
                position=[]
                x = self.jsonInfo[self.firstKey]['regions'][index]['shape_attributes']['all_points_x']
                y = self.jsonInfo[self.firstKey]['regions'][index]['shape_attributes']['all_points_y']
                label = self.jsonInfo[self.firstKey]['regions'][index]['region_attributes']['oral']
                for j in range(len(x)):
                    position.append([x[j], y[j]])    # 取得(x ,y)座標位置
                position_array = np.array([position])# 建立 cv2.ploylines 吃的格式
                image = cv2.polylines(image, [position_array], isClosed=True, color=self.color_dict[label], thickness=line_width)
                cv2.imwrite('Ground_Truth.png', image)
        # show GT image with masks
        ori_bytesPerline = 3 * self.width
        Q = QPixmap(QImage(image, self.width, self.height, ori_bytesPerline, QImage.Format_RGB888).rgbSwapped())
        self.ui.show_1.setPixmap(Q);self.ui.show_1.setScaledContents(True); self.ui.label_show1.setText('Ground Truth Image')
        os.remove('Ground_Truth.png')
    
    def add(self):
        self.add_pos=[]; self.add_x_pos=[]; self.add_y_pos=[];self.add_line=[];self.add_circle=[]
        label = self.select_label(); self.save=True
        self.add_label = ''
        if  label == 0:
            self.add_label = 'G'
        elif label == 1:
            self.add_label = 'R'
        elif label == 2:
            self.add_label = 'Y'
        else:
            pass

    def select_label(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Info")
        msg.setText("Please select a class.")
        msg.addButton('G', QMessageBox.YesRole)  # 0 (int)
        msg.addButton('R', QMessageBox.YesRole)  # 1
        msg.addButton('Y', QMessageBox.YesRole)  # 2
        msg.addButton(QMessageBox.Cancel)
        return msg.exec_() 
    
    def get_clicked_position(self, event):
        self.drag = True
        self.x0 = event.pos().x()
        self.y0 = event.pos().y() 
        self.norm_x0 = self.x0/640
        self.norm_y0 = self.y0/480
        # print(f"(x, y) = ({self.x0}, {self.y0}), normalized (x, y) = ({self.norm_x0}, {self.norm_y0})")
        if self.add_label == '':  # 判斷:若無預先選擇繪製類別，跳出訊息'請先選擇類別'
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle("Info")
            msgBox.setText("Please select a class first.")
            msgBox.addButton(QMessageBox.Ok)
            retval = msgBox.exec_()
        else: 
            self.add_x_pos.append(int(self.width*self.norm_x0)) 
            self.add_y_pos.append(int(self.height*self.norm_y0))
            self.add_pos.append([int(self.width*self.norm_x0), int(self.height*self.norm_y0)])  # draw polygon
            self.add_line.append((int(self.width*self.norm_x0),int(self.height*self.norm_y0)))  # draw line
            self.add_circle.append([int(self.width*self.norm_x0), int(self.height*self.norm_y0)]) # draw circle
            self.__update_add_img()
    
    def __update_add_img(self):
        self.img = cv2.imread('predict.png')
        num_pos = len(self.add_circle)
        for point in self.add_circle:
            cv2.circle(self.img, tuple(point), 3, self.color_dict[self.add_label], -1) # thickness:-1, fill the circle
        if num_pos == 2 :  # 只有兩點，畫線取代
            cv2.line(self.img, self.add_line[0], self.add_line[1], self.color_dict[self.add_label], 1)
        if num_pos >= 3 :  # 大於3個點畫polygon
            self.position_array = np.array(self.add_pos)
            self.img = cv2.polylines(self.img, [self.position_array], isClosed=True
                                    , color=self.color_dict[self.add_label], thickness=1)
        cv2.imwrite('predict_mask.png', self.img)
        self.show2('predict_mask.png')
    
    def enter_save_polygon(self):
        self.enter_x.append(self.add_x_pos)
        self.enter_y.append(self.add_y_pos)
        self.enter_label.append(self.add_label)  #準備用來寫入json的資訊
        self.save = True
        cv2.imwrite('predict.png', self.img)     #更新影像
        self.show2('predict.png')

    def remove_current_polygon(self):         # 清空暫存空間
        self.add_pos=[]; self.add_x_pos=[]; self.add_y_pos=[];self.add_line=[];self.add_circle=[] 
        self.show2('predict.png')

    def save(self):
        if self.save == False:
            # 複製一份到新標註裡
            shutil.copyfile(self.predict_ANN_path, self.new_ANN_path)
        else:
            # convert mask to bounding box
            self.content= []
            for index in range(len(self.enter_label)):
                info = Mask2Bbox(self.enter_x[index], self.enter_y[index]
                                 ,self.class_dic_reverse[self.enter_label[index][0]]
                                 ,self.height, self.width
                                )
                self.content.append(info)
            self.write_txt = self.write_into_txt2 + self.content
            file = open(self.new_ANN_path, 'w')
            for item in list(set(self.write_txt)):
                file.write(item+'\n')
            file.close()

            # save JSON Infos
            rest_of_mask = len(self.jsonInfo[self.firstKey]['regions'])   # 將沒被刪除的mask提取出來(此時新增的mask資訊已經在裡面了)
            save_data = []
            for i in range(rest_of_mask):
                self.enter_x.append(self.jsonInfo[self.firstKey]['regions'][i]['shape_attributes']['all_points_x'])
                self.enter_y.append(self.jsonInfo[self.firstKey]['regions'][i]['shape_attributes']['all_points_y'])
                self.enter_label.append(self.jsonInfo[self.firstKey]['regions'][i]['region_attributes']['oral'])
            print(self.enter_label)
            for i in range(len(self.enter_x)):
                save_data.append({"shape_attributes":{"name":"polygon",
                                                "all_points_x": self.enter_x[i],
                                                "all_points_y": self.enter_y[i]},
                                "region_attributes":{"oral":self.enter_label[i]}}
                                )
            self.jsonInfo[self.firstKey]['regions'] = save_data
        os.remove('predict.png')
        self.content = []; self.save = False
        self.add_pos=[]; self.add_x_pos=[]; self.add_y_pos=[];self.add_line=[];self.add_circle=[]
        self.enter_x=[]; self.enter_y=[]; self.enter_label=[] # 更新儲存內容

    def export(self): # export new version of json file to new annotation folder
        today = datetime.date.today(); now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8)))
        year = today.year; month = today.month; day = today.day
        hour = now.hour; minute = now.minute
        if month < 10:
            month = '0' + str(month)
        if day < 10:
            day = '0' + str(day)
        if hour < 10:
            hour = '0' + str(hour)
        if minute < 10:
            minute = '0' + str(minute)
        date = str(year) + str(month) + str(day) + str(hour) + str(minute)
        versionNumber = str( int(self.JsonFile_path[-6]) +1 )
        save_path = self.dir_path.strip('Original_Image') + 'JSON/' + date + '_' + 'Version' + versionNumber + '.json'
        with open(save_path, 'w') as update:
            json.dump(self.jsonInfo, update)

    # Theme
    def dark_teal(self):
        apply_stylesheet(app, theme='dark_teal.xml')
        
    def light_teal(self):
        apply_stylesheet(app, theme='light_teal.xml')


def draw_bbox(ori_path, txt_path): # 輸入ORI影像路徑及標註檔路徑
    ori_img = cv2.imread(ori_path)
    height, width, channel = ori_img.shape

    # dic
    global class_dic
    class_dic = {0:'G', 1:'R', 2:'Y'}
    color_dic = {0:(0,255,0), 1:(0,0,255), 2:(0,128,255)}
    class_id=[]; x=[]; y=[]; w=[]; h=[]

    #read annotation file
    with open(txt_path) as f:
        for line in f.readlines():
            s = line.split(' ')  
            class_id.append(s[0]); x.append(s[1])
            y.append(s[2]); w.append(s[3]); 
            h.append(s[4].replace('\n', '')) # 去掉換行符號
    for num in range(len(class_id)):
        x0 = float(x[num])*float(width) - float(w[num])*float(width) / 2
        x1 = float(x[num])*float(width) + float(w[num])*float(width) / 2
        y0 = float(y[num])*float(height) - float(h[num])*float(height) / 2
        y1 = float(y[num])*float(height) + float(h[num])*float(height) / 2

        start_point = (int(x0), int(y0))
        end_point = (int(x1), int(y1))
        text_point = (int(x0), int(y0)-10)
        id_point = (int(x0)-20, int(y0)-10)

        text = class_dic[int(class_id[num])]
        color = color_dic[int(class_id[num])]
        id_number = str(num + 1)

        # according to class_id, change the edge color of bounding box
        cv2.rectangle(ori_img, start_point, end_point, color=color, thickness=2)
        # put class_id on the top-left of bounding box
        cv2.putText(ori_img, text, text_point, cv2.FONT_HERSHEY_SIMPLEX,1, color,2, cv2.LINE_AA)
        # put the id number beside the class
        cv2.putText(ori_img, id_number, id_point, cv2.FONT_HERSHEY_SIMPLEX,1, color,2, cv2.LINE_AA)
    cv2.imwrite('predict.png', ori_img)  

def Mask2Bbox(xPoints, yPoints, label, height, width):
    x_max = max(xPoints); x_min = min(xPoints)
    y_max = max(yPoints); y_min = min(yPoints)
    center_x = round((x_min + x_max)/2/width, 6)
    center_y = round((y_min + y_max)/2/height, 6)
    w = round((x_max - x_min)/ width, 6)
    h = round((y_max - y_min)/ height, 6)
    txt=[]; txt.append(label); txt.append(str(center_x))
    txt.append(str(center_y)); txt.append(str(w)); txt.append(str(h))
    write_into_txt = ' '.join(map(str, txt))
    return write_into_txt

if __name__ == '__main__':
    app =  QtWidgets.QApplication(sys.argv)
    window = MainWindow_controller()
    window.show()

    # setup stylesheet
    apply_stylesheet(app, theme='dark_teal.xml')
    sys.exit(app.exec_())




# self.dir_path：資料夾的絕對路徑
# self.clickedItem: 點擊的檔名
# 資料夾檔名不要用中文，會讀不到影像路徑

#-----------------Bugs-------------------------
# 0309 --> 不同附檔名開啟的問題 --> solved
# 0328 --> 單純按下save會有閃退的問題 
# 0329 --> 醫師要求標註完成後跳下一張影像再跳回來後，可以及時顯示上次的標註結果(去掉mask,轉成Bbox) --> solved
# 0329 --> 按下save current polygon 後，欲刪除其他bbox會連同mask一起消失 unsolved 

# 必須選擇影像資料夾與標註檔，才能進行下一步，否則將會閃退。