# 簡介:
本專案是一個基於Python的棒球紀錄系統開發專案，針對60FPS的影片，偵測投手投球的軌跡與進壘點，輔助相關人員紀錄賽事表現並提升作業效率。    
![demo](https://github.com/user-attachments/assets/274f601f-6839-482b-92c7-ebac2615efbe)  

# 環境:
建議於python3.8+中執行，所需要安裝的套件請見[/docs/requirements.txt](https://github.com/C-H-Chen/baseball-trajectory-recorder/blob/main/docs/requirements.txt)。   

# Demo說明:  
以下是完整Demo的影片，並會針對影片中的各個重點步驟於下方進行說明。  
[Demo Video](https://github.com/user-attachments/assets/42b28758-cf5d-45fa-8b9e-b0cd29813e38)    
######  Step 1.  
輸入下列指令執行OpenPose，目的是為了獲得人體的關鍵點，用以建構好球帶的偵測區域。 

    bin\OpenPoseDemo.exe --video {VIDEO_PATH} --write_json output_jsons/       
![image](https://github.com/user-attachments/assets/7b8422ea-7835-4ed1-88ec-1793677f26ee)
######  Step 2.
如下圖標示，於main.py中輸入OpenPose輸出的json檔名，並根據影片中的打者與打擊慣用手適時修改輸入對象與關鍵點的索引值。  
![1](https://github.com/user-attachments/assets/e6abd71d-f7d5-413b-89da-e6eb46cb9d9a)  
![2](https://github.com/user-attachments/assets/d076af70-1d78-4ceb-98e2-2e77a9988844)

######  Step 3.
輸入下列指令執行核心程式。

    python main.py -v {VIDEO_PATH}  
######  Step 4. 
指令執行後，滑鼠點擊畫面本壘板兩側建立偵測區域，即可開始進行偵測。  
![image](https://github.com/user-attachments/assets/4a567b04-0f21-4c70-9cfc-c2867caa4926)

# 輸出解釋:  

