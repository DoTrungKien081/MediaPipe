import ctypes;
import ctypes.util;
import cv2;
import mediapipe as mp;
from mediapipe.tasks import python;
from mediapipe.tasks.python import vision;
import math;
from pathlib import Path;
import shutil;
import subprocess;
import time;

FACE_CONFIDENCE = 0.5;
HAND_CONFIDENCE = 0.5;
APP_DIR = Path(__file__).resolve().parent;

def assetPath(relativePath):
    path = APP_DIR / relativePath;
    if not path.is_file():
        raise FileNotFoundError(f"Required application asset was not found: {path}");
    return str(path);

def calcDist(p1, p2):
    return math.hypot(p2.x - p1.x, p2.y - p1.y);

def maximizeWindow(windowId):
    class ClientMessageData(ctypes.Union):
        _fields_ = [
            ("bytes", ctypes.c_char * 20),
            ("shorts", ctypes.c_short * 10),
            ("longs", ctypes.c_long * 5)
        ];

    class ClientMessageEvent(ctypes.Structure):
        _fields_ = [
            ("type", ctypes.c_int),
            ("serial", ctypes.c_ulong),
            ("send_event", ctypes.c_int),
            ("display", ctypes.c_void_p),
            ("window", ctypes.c_ulong),
            ("message_type", ctypes.c_ulong),
            ("format", ctypes.c_int),
            ("data", ClientMessageData)
        ];

    class XEvent(ctypes.Union):
        _fields_ = [
            ("type", ctypes.c_int),
            ("client_message", ClientMessageEvent),
            ("padding", ctypes.c_long * 24)
        ];

    libraryPath = ctypes.util.find_library("X11");
    if libraryPath is None:
        raise RuntimeError("The X11 library is required to maximize the camera window.");
    x11 = ctypes.CDLL(libraryPath);
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p];
    x11.XOpenDisplay.restype = ctypes.c_void_p;
    x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p];
    x11.XDefaultRootWindow.restype = ctypes.c_ulong;
    x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int];
    x11.XInternAtom.restype = ctypes.c_ulong;
    x11.XSendEvent.argtypes = [
        ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long,
        ctypes.POINTER(XEvent)
    ];
    x11.XSendEvent.restype = ctypes.c_int;
    x11.XFlush.argtypes = [ctypes.c_void_p];
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p];

    display = x11.XOpenDisplay(None);
    if not display:
        raise RuntimeError("Could not connect to the X11 display to maximize the camera window.");

    event = XEvent();
    # Request a window-manager maximize state without switching to fullscreen.
    event.client_message.type = 33;
    event.client_message.send_event = 1;
    event.client_message.display = display;
    event.client_message.window = int(windowId);
    event.client_message.message_type = x11.XInternAtom(display, b"_NET_WM_STATE", False);
    event.client_message.format = 32;
    event.client_message.data.longs[0] = 1;
    event.client_message.data.longs[1] = x11.XInternAtom(
        display, b"_NET_WM_STATE_MAXIMIZED_VERT", False
    );
    event.client_message.data.longs[2] = x11.XInternAtom(
        display, b"_NET_WM_STATE_MAXIMIZED_HORZ", False
    );
    event.client_message.data.longs[3] = 1;

    rootWindow = x11.XDefaultRootWindow(display);
    sent = x11.XSendEvent(
        display, rootWindow, False, (1 << 20) | (1 << 19), ctypes.byref(event)
    );
    x11.XFlush(display);
    x11.XCloseDisplay(display);
    if not sent:
        raise RuntimeError("The window manager did not accept the maximize request.");

def identifyMeme(faceLandmarks, handLandmarks):
    hands = sorted(handLandmarks, key=lambda hand: hand[0].x);

    def hand_scale(hand):
        return calcDist(hand[0], hand[9]);

    def extended_by_distance(hand, tipIndex, jointIndex):
        return (
            calcDist(hand[0], hand[tipIndex]) - calcDist(hand[0], hand[jointIndex])
            > max(hand_scale(hand) * 0.1, 0.004)
        );

    def finger_extended(hand, tipIndex, jointIndex):
        return extended_by_distance(hand, tipIndex, jointIndex);

    def extended_finger_count(hand):
        return sum(
            finger_extended(hand, tip, joint)
            for tip, joint in [(8, 6), (12, 10), (16, 14), (20, 18)]
        );

    def thumb_extended(hand):
        return extended_by_distance(hand, 4, 3);

    def closed_fist(hand):
        return (
            extended_finger_count(hand) == 0
            and calcDist(hand[4], hand[9]) < hand_scale(hand) * 0.75
        );

    def thumb_up(hand):
        return (
            thumb_extended(hand)
            and hand[4].y < hand[2].y - max(hand_scale(hand) * 0.1, 0.005)
            and hand[4].y < hand[0].y
            and extended_finger_count(hand) == 0
            and not closed_fist(hand)
        );

    def open_palm(hand):
        return thumb_extended(hand) and extended_finger_count(hand) == 4;

    if faceLandmarks is not None and len(hands) == 2:
        earPoints = sorted([faceLandmarks[127], faceLandmarks[356]], key=lambda point: point.x);
        faceSides = sorted([faceLandmarks[234], faceLandmarks[454]], key=lambda point: point.x);
        faceWidth = max(
            faceSides[1].x - faceSides[0].x,
            0.01
        );
        nearBothEars = all(
            min(calcDist(point, ear) for point in hand) < faceWidth * 0.25
            for hand, ear in zip(hands, earPoints)
        );
        if nearBothEars:
            return "SHOCKED";

    if len(hands) == 2 and all(open_palm(hand) for hand in hands):
        return "ABSOLUTE_CINEMA";

    if faceLandmarks is not None and hands:
        earPairs = [
            (faceLandmarks[127], faceLandmarks[234]),
            (faceLandmarks[356], faceLandmarks[454])
        ];
        for hand in hands:
            pointingFingers = [
                tip for tip, joint in [(8, 6), (12, 10), (16, 14), (20, 18)]
                if finger_extended(hand, tip, joint)
            ];
            if not 1 <= len(pointingFingers) <= 2:
                continue;
            pointsAtTemple = any(
                calcDist(hand[tip], earPoint)
                <= 2.5 * calcDist(earPoint, otherEarPoint)
                for tip in pointingFingers
                for earPoint, otherEarPoint in earPairs
            );
            if pointsAtTemple:
                return "USE_YOUR_BRAIN";

    if faceLandmarks is not None and hands:
        mouthX = (faceLandmarks[13].x + faceLandmarks[14].x) / 2;
        mouthY = (faceLandmarks[13].y + faceLandmarks[14].y) / 2;
        faceSides = sorted([faceLandmarks[234], faceLandmarks[454]], key=lambda point: point.x);
        faceWidth = max(faceSides[1].x - faceSides[0].x, 0.01);
        nearMouth = any(
            min(math.hypot(point.x - mouthX, point.y - mouthY) for point in hand)
            < faceWidth * 0.2
            for hand in hands
        );
        if nearMouth:
            return "THINKING_MONKEY";

    if len(hands) == 1:
        hand = hands[0];
        fingerCount = extended_finger_count(hand);
        indexPointingUp = (
            finger_extended(hand, 8, 6)
            and fingerCount == 1
            and not closed_fist(hand)
            and hand[8].y < hand[6].y - max(hand_scale(hand) * 0.1, 0.005)
            and hand[8].y < hand[0].y
            and hand[8].y < hand[5].y
        );
        if indexPointingUp:
            return "MONKEY_HAS_AN_IDEA";
        if fingerCount == 1:
            return "THINKING_MONKEY";
        if closed_fist(hand):
            return "SPEECHLESS_CAT";

    for hand in hands:
        if thumb_up(hand):
            return "LIKE_CAT";

    if faceLandmarks is None:
        return "SPEECHLESS_CAT";

    return "SPEECHLESS_CAT";

def overlayMeme(bg, overlay, x, y):
    ovHeight = overlay.shape[0];
    ovWidth = overlay.shape[1];
    bgHeight = bg.shape[0];
    bgWidth = bg.shape[1];
    topLeftX = int(x - ovWidth / 2);
    topLeftY = int(y - ovHeight / 2);
    startX = max(0, topLeftX);
    startY = max(0, topLeftY);
    endX = min(bgWidth, topLeftX + ovWidth);
    endY = min(bgHeight, topLeftY + ovHeight);
    ovStartX = startX - topLeftX;
    ovStartY = startY - topLeftY;
    ovEndX = ovStartX + (endX - startX);
    ovEndY = ovStartY + (endY - startY);
    if startX < endX and startY < endY:
        overlayCrop = overlay[ovStartY:ovEndY, ovStartX:ovEndX];
        bgCrop = bg[startY:endY, startX:endX];
        if len(overlay.shape) == 3 and overlay.shape[2] == 4:
            alpha = overlayCrop[:, :, 3] / 255.0;
            alphaInv = 1.0 - alpha;
            for c in range(0, 3):
                bgCrop[:, :, c] = (alpha * overlayCrop[:, :, c] + alphaInv * bgCrop[:, :, c]);
        else:
            bg[startY:endY, startX:endX] = overlayCrop[:, :, :3];
    return bg;

def loadAndResizeMeme(path, size):
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED);
    if img is None:
        raise FileNotFoundError(f"Unable to load meme image: {path}");
    img = cv2.resize(img, (size, size));
    return img;

imgShocked = loadAndResizeMeme(assetPath("MemeLib/Shocked.jpg"), 200);
imgCinema = loadAndResizeMeme(assetPath("MemeLib/AbsoluteCinema.png"), 200);
imgRoll = loadAndResizeMeme(assetPath("MemeLib/UseYourBrain.jpg"), 200);
imgThinkingMonkey = loadAndResizeMeme(assetPath("MemeLib/ThinkingMonkey.jpeg"), 200);
imgSpeechlessCat = loadAndResizeMeme(assetPath("MemeLib/SpeechlessCat.jpg"), 200);
imgMonkeyIdea = loadAndResizeMeme(assetPath("MemeLib/MonkeyHasAnIdea.jpg"), 200);
imgLikeCat = loadAndResizeMeme(assetPath("MemeLib/LikeCat.jpg"), 200);

faceOptions = vision.FaceLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path=assetPath("face_landmarker.task")),
    running_mode=vision.RunningMode.VIDEO,
    min_face_detection_confidence=FACE_CONFIDENCE,
    min_face_presence_confidence=FACE_CONFIDENCE,
    min_tracking_confidence=FACE_CONFIDENCE
);
faceDetector = vision.FaceLandmarker.create_from_options(faceOptions);
handOptions = vision.HandLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path=assetPath("hand_landmarker.task")),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=HAND_CONFIDENCE,
    min_hand_presence_confidence=HAND_CONFIDENCE,
    min_tracking_confidence=HAND_CONFIDENCE
);
handDetector = vision.HandLandmarker.create_from_options(handOptions);

cap = cv2.VideoCapture(0);
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640);
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360);
windowName = "Meme Recognizer App";
cv2.namedWindow(windowName, cv2.WINDOW_NORMAL);
windowSized = False;
windowMaximized = False;
windowManagerTool = shutil.which("xdotool");

while True:
    success, img = cap.read();
    if not success:
        break;
    if not windowSized:
        cv2.resizeWindow(windowName, img.shape[1], img.shape[0]);
        windowSized = True;
    img = cv2.flip(img, 1);
    imgRgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB);
    mpImage = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRgb);
    timestampMs = time.monotonic_ns() // 1_000_000;
    faceResult = faceDetector.detect_for_video(mpImage, timestampMs);
    handResult = handDetector.detect_for_video(mpImage, timestampMs);
    faceLandmarks = faceResult.face_landmarks[0] if faceResult.face_landmarks else None;
    detectedMeme = identifyMeme(faceLandmarks, handResult.hand_landmarks);

    activeMeme = None;
    if detectedMeme == "SHOCKED":
        activeMeme = imgShocked;
    elif detectedMeme == "ABSOLUTE_CINEMA":
        activeMeme = imgCinema;
    elif detectedMeme == "USE_YOUR_BRAIN":
        activeMeme = imgRoll;
    elif detectedMeme == "THINKING_MONKEY":
        activeMeme = imgThinkingMonkey;
    elif detectedMeme == "SPEECHLESS_CAT":
        activeMeme = imgSpeechlessCat;
    elif detectedMeme == "MONKEY_HAS_AN_IDEA":
        activeMeme = imgMonkeyIdea;
    elif detectedMeme == "LIKE_CAT":
        activeMeme = imgLikeCat;

    if activeMeme is not None:
        memeX = int(img.shape[1] - (activeMeme.shape[1] / 2));
        memeY = int(activeMeme.shape[0] / 2);
        img = overlayMeme(img, activeMeme, memeX, memeY);

    cv2.imshow(windowName, img);

    key = cv2.waitKey(1) & 0xFF;
    if not windowMaximized and windowManagerTool:
        windowIds = subprocess.run(
            [windowManagerTool, "search", "--onlyvisible", "--name", f"^{windowName}$"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.splitlines();
        if windowIds:
            maximizeWindow(windowIds[0]);
            windowMaximized = True;
    if cv2.getWindowProperty(windowName, cv2.WND_PROP_VISIBLE) < 1:
        break;

cap.release();
handDetector.close();
faceDetector.close();
cv2.destroyAllWindows();
