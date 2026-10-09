
from ultralytics import YOLO
import cv2
import os

# Load the trained YOLO model
model_path = "outputs/yolo/road_pothole_yolo/weights/best.pt"
model = YOLO(model_path)

# Enter the path of the road image to test
image_path = input("Enter road image path: ").strip().strip('"')

# Check whether the image exists
if not os.path.exists(image_path):
    print("Error: Image file not found!")
    exit()

# Run pothole detection
results = model.predict(
    source=image_path,
    conf=0.25,
    save=True
)

# Display the detected potholes
for result in results:
    image = result.plot()
    cv2.imshow("YOLO Pothole Detection", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

print("Detection completed!")
print("Check the runs/detect folder for the output image.")
