import pickle

import cvzone
import numpy as np
from flask import Flask, render_template, Response
import cv2

app = Flask(__name__)
cap = cv2.VideoCapture('carPark.mp4')

width, height = 132, 58

# with open("carParkPos", "rb") as f:
#     posList = pickle.load(f)

try:
    with open("carParkPos", "rb") as f:
        posList = pickle.load(f)
except:
    posList = []


def checkParkingSpace(imgPro, img):

    spaceCounter = 0
    # cv2.rectangle(img, (38, 162), (170, 220), (255, 0, 255), 2)
    for pos in posList:
        x, y = pos

        imgCrop = imgPro[y:y+height, x: x+width]
        # cv2.imshow(str(x*y), imgCrop)
        count = cv2.countNonZero(imgCrop)

        if count < 900:
            color = (0, 255, 0)
            thickness = 5
            spaceCounter += 1
        else:
            color = (0, 0, 255)
            thickness = 2
        cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness=thickness)
        cvzone.putTextRect(img, str(count), (x, y+height - 3), scale=1, thickness=2, offset=0, colorR=color)

    cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20, colorR=(0, 200, 0))


def generate_frames():
    # while True:
    #
    #     ## read the camera frame
    #     success, frame = camera.read()
    #     if not success:
    #         break
    #     else:
    #         ret, buffer = cv2.imencode('.jpg', frame)
    #         frame = buffer.tobytes()
    while True:

        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        success, img = cap.read()
        if not success:
            break
        else:
            # Thresholding the image
            imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
            imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
            imgMedian = cv2.medianBlur(imgThreshold, 5)
            kernel = np.ones((3, 3), np.uint8)
            imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)
            #
            checkParkingSpace(imgDilate, img)
            # checkParkingSpace(img)

            # cv2.imshow('Image', img)
            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()


        # for pos in posList:
        #     cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), (255, 0, 255), 2)

        # cv2.imshow('Image', img)
        # cv2.imshow('ImageBlur', imgBlur)
        # cv2.imshow('ImageThresh', imgThreshold )
        # cv2.imshow('ImageMedian', imgMedian )

        # ret, buffer = cv2.imencode('.jpg', img)
        # frame = buffer.tobytes()

        # cv2.waitKey(10)
        # return frame

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def mouseClick(events, x, y, flags, params):
    if events == cv2.EVENT_LBUTTONDOWN:
        posList.append((x, y))
    if events == cv2.EVENT_RBUTTONDOWN:
        for i, pos in enumerate(posList):
            x1, y1 = pos
            if x1 < x < x1 + width and y1 < y < y1 + height:
                posList.pop(i)

    with open("carParkPos", "wb") as f:
        pickle.dump(posList, f)

def admin_frames():
    while True:
        img = cv2.imread("carParking.png")
        #
        # cv2.rectangle(img, (38, 162), (170, 220), (255, 0, 255), 2)
        for pos in posList:
            cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), (255, 0, 255), 2)
        #
        # # cv2.imshow("Image", img)
        ret, buffer = cv2.imencode('.jpg', img)
        frame = buffer.tobytes()
        # cv2.setMouseCallback("Image", mouseClick)
        #
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        # cv2.waitKey(1)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/admin')
def admin():
    return Response(admin_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True)