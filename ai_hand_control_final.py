import cv2
import time
import os
import numpy as np
import pyautogui
import mediapipe as mp
import subprocess

# dont lock me out lol
pyautogui.FAILSAFE = False

# screen size setup
w_scrn, h_scrn = pyautogui.size()

cam = cv2.VideoCapture(0)
cam.set(3, 640)
cam.set(4, 480)

# mediapipe stuff
mp_hnds = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# setup hand trackin
hnd_mod = mp_hnds.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# for smooth movemnt
last_x, last_y = 0, 0
smth_val = 7
is_dragn = False
gest_timer = {"yt": None, "clk": None, "dual": None}
wait_1h = 5.0 
wait_2h = 10.0 

def get_fngrs(pts):
    fngs = []
    # thumb check
    fngs.append(pts[4].x < pts[3].x) 
    # others
    for tip, pip in [(8,6),(12,10),(16,14),(20,18)]:
        fngs.append(pts[tip].y < pts[pip].y)
    return fngs

while True:
    sucess, frame = cam.read()
    if not sucess:
        break
    frame = cv2.flip(frame, 1)
    fh, fw, _ = frame.shape

    # convert for mediapipe
    rgb_vid = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hnd_mod.process(rgb_vid)

    msg = ""
    curr_t = time.time()

    # two hands logic
    if results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 2:
        if gest_timer["dual"] is None:
            gest_timer["dual"] = curr_t
        elif curr_t - gest_timer["dual"] >= wait_2h:
            subprocess.Popen(['notepad.exe'])
            time.sleep(0.5)
            pyautogui.typewrite("Ankita Bolod", interval=0.1)
            msg = "Both Hands -> Note"
            gest_timer["dual"] = None
            gest_timer["yt"] = None
            gest_timer["clk"] = None

    # single hand logic
    elif results.multi_hand_landmarks and len(results.multi_hand_landmarks) == 1:
        hnd_pts = results.multi_hand_landmarks[0]
        lmrk = hnd_pts.landmark
        mp_draw.draw_landmarks(frame, hnd_pts, mp_hnds.HAND_CONNECTIONS)

        f_up = get_fngrs(lmrk)
        thmb, indx, midl, rng, pky = f_up

        idx_x, idx_y = int(lmrk[8].x * fw), int(lmrk[8].y * fh)
        thmb_x, thmb_y = int(lmrk[4].x * fw), int(lmrk[4].y * fh)

        # check pinch gap
        gap = np.hypot(thmb_x - idx_x, thmb_y - idx_y)

        # mouse move
        if all(f_up):
            target_x = np.interp(idx_x, [0, fw], [0, w_scrn])
            target_y = np.interp(idx_y, [0, fh], [0, h_scrn])
            
            # ease the movement
            move_x = last_x + (target_x - last_x) / smth_val
            move_y = last_y + (target_y - last_y) / smth_val
            
            pyautogui.moveTo(move_x, move_y)
            last_x, last_y = move_x, move_y
            msg = "Moving Cursor"
            is_dragn = False
            gest_timer["yt"] = None
            gest_timer["clk"] = None

        # pinch to drag
        elif gap < 30:
            if not is_dragn:
                pyautogui.mouseDown()
                is_dragn = True
            
            target_x = np.interp(idx_x, [0, fw], [0, w_scrn])
            target_y = np.interp(idx_y, [0, fh], [0, h_scrn])
            move_x = last_x + (target_x - last_x) / smth_val
            move_y = last_y + (target_y - last_y) / smth_val
            
            pyautogui.moveTo(move_x, move_y)
            last_x, last_y = move_x, move_y
            msg = "Dragging..."
            gest_timer["yt"] = None
            gest_timer["clk"] = None

        else:
            if is_dragn:
                pyautogui.mouseUp()
                is_dragn = False
            
            # index finger only -> youtube
            if indx and not midl and not rng and not pky:
                if gest_timer["yt"] is None:
                    gest_timer["yt"] = curr_t
                elif curr_t - gest_timer["yt"] >= wait_1h:
                    os.system("start https://www.youtube.com")
                    msg = "Opening YT"
                    gest_timer["yt"] = None
            else:
                gest_timer["yt"] = None

            # index + middle -> click
            if indx and midl and not rng and not pky:
                if gest_timer["clk"] is None:
                    gest_timer["clk"] = curr_t
                elif curr_t - gest_timer["clk"] >= wait_1h:
                    pyautogui.click()
                    msg = "Clicked!"
                    gest_timer["clk"] = None
            else:
                gest_timer["clk"] = None

        if gap < 40:
            cv2.circle(frame, (idx_x, idx_y), 15, (0,0,255), cv2.FILLED)

    cv2.putText(frame, msg, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.imshow("Handy Control", frame)

    if cv2.waitKey(1) & 0xFF == 27: # esc to quit
        break

cam.release()
cv2.destroyAllWindows()