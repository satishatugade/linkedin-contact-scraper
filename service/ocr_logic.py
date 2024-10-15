
# import cv2
# import pytesseract
# import psycopg2
# import os
# from datetime import datetime
# import pytz

# # Path to Tesseract executable
# pytesseract.pytesseract.tesseract_cmd = r'D:\\Tesseract-OCR\\tesseract.exe'

# # Connect to PostgreSQL database
# def connect_db():
#     try:
#         conn = psycopg2.connect(
#             dbname="uq_eventible",
#             user="postgres",
#             password="123456789",
#             host="localhost",
#             port="5432"
#         )
#         return conn
#     except Exception as e:
#         print(f"Error connecting to database: {e}")
#         return None

# # Save extracted information to database
# def save_to_db(conn, name, occupation, location, sddh_id):
#     try:
#         timezone = pytz.timezone("Asia/Kolkata")
#         created_date = datetime.now(timezone)

#         with conn.cursor() as cursor:
#             cursor.execute(
#                 """
#                 INSERT INTO uq_event_contact_info (contact_name, occupation, location, sddh_id, created_date)
#                 VALUES (%s, %s, %s, %s, %s)
#                 """,
#                 (name, occupation, location, sddh_id, created_date)
#             )
#             conn.commit()
#             print(f"Saved to DB: {name}, {occupation}, {location}, {sddh_id}")
#     except Exception as e:
#         print(f"Error saving to database: {e}")

# # Click and crop event handler
# def click_and_crop(event, x, y, flags, param):
#     global ref_points, cropping

#     if event == cv2.EVENT_LBUTTONDOWN:
#         ref_points = [(x, y)]
#         cropping = True

#     elif event == cv2.EVENT_LBUTTONUP:
#         ref_points.append((x, y))
#         cropping = False
#         cv2.rectangle(image, ref_points[0], ref_points[1], (0, 255, 0), 2)
#         cv2.imshow("image", image)

# # Function to manually select coordinates on the image
# def get_coordinates(image_path):
#     global image, ref_points

#     if not os.path.exists(image_path):
#         print(f"Image file not found: {image_path}")
#         return None

#     image = cv2.imread(image_path)
#     if image is None:
#         print(f"Failed to read the image at: {image_path}")
#         return None

#     clone = image.copy()
#     ref_points = []
#     cv2.namedWindow("image")
#     cv2.setMouseCallback("image", click_and_crop)

#     while True:
#         cv2.imshow("image", image)
#         key = cv2.waitKey(1) & 0xFF
#         if key == 8:  # Press Backspace to reset coordinates
#             image = clone.copy()
#             ref_points = []
#         elif key == 13:  # Press Enter to finish selection
#             break

#     cv2.destroyAllWindows()

#     if len(ref_points) == 2:
#         return ref_points
#     else:
#         print("No valid coordinates selected.")
#         return None


# def process_image(image_path, coords, conn, sddh_id):
#     image = cv2.imread(image_path)
#     clone = image.copy()

#     if image is None:
#         print(f"Image not found: {image_path}")
#         return

#     for i, (start, end) in enumerate(coords):
#         roi = clone[start[1]:end[1], start[0]:end[0]]
#         text = pytesseract.image_to_string(roi)

#         lines = [line.strip() for line in text.splitlines() if line.strip()]
#         name = lines[0] if len(lines) > 0 else ""
#         occupation = lines[1] if len(lines) > 1 else ""
#         location = lines[2] if len(lines) > 2 else ""

#         print(f"OCR Result for {os.path.basename(image_path)}:")
#         print(f"Name: {name}")
#         print(f"Occupation: {occupation}")
#         print(f"Location: {location}")
#         print('-' * 50)

#         if conn:
#             save_to_db(conn, name, occupation, location, sddh_id)


# def main(root_folder):
#     conn = connect_db()
#     selected_subfolder = os.listdir(root_folder)[0]  
#     selected_subfolder_path = os.path.join(root_folder, selected_subfolder)
#     sddh_id = selected_subfolder  
#     print(f"Selected sddh_id: {sddh_id}")

#     # before_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_page_1_before_scroll.png")
#     # after_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_page_1_after_scroll.png")

#     before_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_before_scroll_page_1.png")
#     after_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_after_scroll_page_1.png")

#     print("Please select coordinates for the 'before_scroll' image:")
#     coordinates_before_scroll = get_coordinates(before_scroll_image_path)

   
#     print("Please select coordinates for the 'after_scroll' image:")
#     coordinates_after_scroll = get_coordinates(after_scroll_image_path)

#     if not coordinates_before_scroll or not coordinates_after_scroll:
#         print("Failed to get coordinates. Exiting.")
#         return

    
#     for subfolder in os.listdir(root_folder):
#         subfolder_path = os.path.join(root_folder, subfolder)

#         if not os.path.isdir(subfolder_path):
#             continue

#         sddh_id = subfolder  
#         print(f"Processing sddh_id: {sddh_id}")
#         page_number = 1
#         while True:
#             before_scroll_image = os.path.join(subfolder_path, f"{subfolder}_page_{page_number}_before_scroll.png")
#             after_scroll_image = os.path.join(subfolder_path, f"{subfolder}_page_{page_number}_after_scroll.png")

#             if os.path.exists(before_scroll_image) and os.path.exists(after_scroll_image):
#                 process_image(before_scroll_image, [coordinates_before_scroll], conn, sddh_id)
#                 process_image(after_scroll_image, [coordinates_after_scroll], conn, sddh_id)
#             else:
#                 break

#             page_number += 1

#     if conn:
#         conn.close()
import cv2
import pytesseract
import psycopg2
import os
from datetime import datetime
import pytz

import inspect
import utils.logging as logger

# pytesseract.pytesseract_cmd = r'D:\\Tesseract-OCR\\tesseract.exe'




def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="uq_eventible",
            user="postgres",
            password="123456789",
            host="localhost",
            port="5432"
        )
        logger.log_message("Successfully connected to the database.", level='info')
        return conn
    except Exception as e:
        logger.log_message(f"Error connecting to database: {e}", level='error', error=str(e))
        return None

# Save extracted information to database
def save_to_db(conn, name, occupation, location, sddh_id):
    try:
        timezone = pytz.timezone("Asia/Kolkata")
        created_date = datetime.now(timezone)

        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO uq_event_contact_info (contact_name, occupation, location, sddh_id, created_date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (name, occupation, location, sddh_id, created_date)
            )
            conn.commit()
            logger.log_message(f"Saved to DB: Name: {name}, Occupation: {occupation}, Location: {location}, sddh_id: {sddh_id}", level='info')
    except Exception as e:
        logger.log_message(f"Error saving to database: {e}", level='error', error=str(e))

# Click and crop event handler
def click_and_crop(event, x, y, flags, param):
    global ref_points, cropping

    if event == cv2.EVENT_LBUTTONDOWN:
        ref_points = [(x, y)]
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:
        ref_points.append((x, y))
        cropping = False
        cv2.rectangle(image, ref_points[0], ref_points[1], (0, 255, 0), 2)
        cv2.imshow("image", image)

# Function to manually select coordinates on the image
def get_coordinates(image_path):
    global image, ref_points

    if not os.path.exists(image_path):
        logger.log_message(f"Image file not found: {image_path}", level='error')
        print(f"Image file not found: {image_path}")
        return None

    image = cv2.imread(image_path)
    if image is None:
        logger.log_message(f"Failed to read the image at: {image_path}", level='error')
        print(f"Failed to read the image at: {image_path}")
        return None

    clone = image.copy()
    ref_points = []
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", click_and_crop)

    while True:
        cv2.imshow("image", image)
        key = cv2.waitKey(1) & 0xFF
        if key == 8:  # Press Backspace to reset coordinates
            image = clone.copy()
            ref_points = []
        elif key == 13:  # Press Enter to finish selection
            break

    cv2.destroyAllWindows()

    if len(ref_points) == 2:
        logger.log_message(f"Coordinates selected: {ref_points}", level='info')
        return ref_points
    else:
        logger.log_message(f"No valid coordinates selected.", level='error')
        print("No valid coordinates selected.")
        return None

# Process the image and extract text using Tesseract OCR
def process_image(image_path, coords, conn, sddh_id):
    image = cv2.imread(image_path)
    clone = image.copy()

    if image is None:
        logger.log_message(f"Image not found: {image_path}", level='error')
        print(f"Image not found: {image_path}")
        return

    for i, (start, end) in enumerate(coords):
        roi = clone[start[1]:end[1], start[0]:end[0]]
        text = pytesseract.image_to_string(roi)

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        name = lines[0] if len(lines) > 0 else ""
        occupation = lines[1] if len(lines) > 1 else ""
        location = lines[2] if len(lines) > 2 else ""

        logger.log_message(f"OCR Result for {os.path.basename(image_path)}: Name: {name}, Occupation: {occupation}, Location: {location}", level='info')
        print(f"OCR Result for {os.path.basename(image_path)}: Name: {name}, Occupation: {occupation}, Location: {location}")
        print('-' * 50)

        if conn:
            save_to_db(conn, name, occupation, location, sddh_id)


def main(root_folder):
    conn = connect_db()
    if not conn:
        logger.log_message(f"Failed to connect to database. Exiting.", level='error')
        return

    selected_subfolder = os.listdir(root_folder)[0]
    selected_subfolder_path = os.path.join(root_folder, selected_subfolder)
    sddh_id = selected_subfolder
    logger.log_message(f"Selected subfolder: {selected_subfolder}, sddh_id: {sddh_id}", level='info')
    print(f"Selected sddh_id: {sddh_id}")

    before_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_before_scroll_page_1.png")
    after_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_after_scroll_page_1.png")

    print("Please select coordinates for the 'before_scroll' image:")
    coordinates_before_scroll = get_coordinates(before_scroll_image_path)

    print("Please select coordinates for the 'after_scroll' image:")
    coordinates_after_scroll = get_coordinates(after_scroll_image_path)

    if not coordinates_before_scroll or not coordinates_after_scroll:
        logger.log_message(f"Failed to get coordinates. Exiting.", level='error')
        print("Failed to get coordinates. Exiting.")
        return

    for subfolder in os.listdir(root_folder):
        subfolder_path = os.path.join(root_folder, subfolder)

        if not os.path.isdir(subfolder_path):
            continue

        sddh_id = subfolder
        logger.log_message(f"Processing sddh_id: {sddh_id}", level='info')
        print(f"Processing sddh_id: {sddh_id}")
        page_number = 1
        while True:
            print()
            before_scroll_image = os.path.join(subfolder_path, f"{subfolder}_page_{page_number}_before_scroll.png")
            after_scroll_image = os.path.join(subfolder_path, f"{subfolder}_page_{page_number}_after_scroll.png")

            if os.path.exists(before_scroll_image) and os.path.exists(after_scroll_image):
                process_image(before_scroll_image, [coordinates_before_scroll], conn, sddh_id)
                process_image(after_scroll_image, [coordinates_after_scroll], conn, sddh_id)
            else:
                break

            page_number += 1

    if conn:
        conn.close()
        logger.log_message(f"Database connection closed.", level='info')
