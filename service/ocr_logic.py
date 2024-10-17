
# import cv2
# import pytesseract
# import os
# from datetime import datetime
# import pytz
# import utils.logging as logger
# import config.database_config as DB

# # pytesseract.pytesseract_cmd = r'D:\\Tesseract-OCR\\tesseract.exe'


# def save_to_db(name, occupation, location, sddh_id):
# # Save extracted information to database
#     conn = DB.database_connection()
#     if not conn:
#         logger.log_message(f"Failed to connect to database. Exiting.", level='error')
#         return
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
#             logger.log_message(f"Saved to DB: Name: {name}, Occupation: {occupation}, Location: {location}, sddh_id: {sddh_id}", level='info')
#     except Exception as e:
#         logger.log_message(f"Error saving to database: {e}", level='error', error=str(e))


# ref_points = []
# cropping = False

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
#         if key == 8:  
#             image = clone.copy()
#             ref_points = []

#         elif key == 13:  
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

# def ocr_scrapping_save(root_folder):
   

#     selected_subfolder = os.listdir(root_folder)[0]
#     selected_subfolder_path = os.path.join(root_folder, selected_subfolder)
#     sddh_id = selected_subfolder
#     logger.log_message(f"Selected subfolder: {selected_subfolder}, sddh_id: {sddh_id}", level='info')
#     print(f"Selected sddh_id: {sddh_id}")

#     before_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_before_scroll_page_1.png")
#     after_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_after_scroll_page_1.png")
#     # before_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_page_2_before_scroll.png")
#     # after_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_page_2_after_scroll.png")

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
#                 process_image(before_scroll_image, [coordinates_before_scroll], sddh_id)
#                 process_image(after_scroll_image, [coordinates_after_scroll], sddh_id)
#             else:
              
#                 break

#             page_number += 1

import cv2
import pytesseract
import os
from datetime import datetime
import pytz
import utils.logging as logger  # Assuming you have a logging utility
import config.database_config as DB


def save_to_db(conn, name, occupation, location, sddh_id):
    """
    Save extracted information to the database.
    """
    if not conn:
        logger.log_message(f"Failed to connect to database. Exiting.", level='error')
        return
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


ref_points = []
cropping = False


def click_and_crop(event, x, y, flags, param):
    global ref_points, cropping

    if event == cv2.EVENT_LBUTTONDOWN:
        logger.log_message(f"Mouse button down at coordinates ({x}, {y}).", level='info')
        ref_points = [(x, y)]
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:
        ref_points.append((x, y))
        cropping = False
        logger.log_message(f"Mouse button up at coordinates ({x}, {y}). Cropping completed.", level='info')
        cv2.rectangle(image, ref_points[0], ref_points[1], (0, 255, 0), 2)
        cv2.imshow("image", image)


def get_coordinates(image_path):
    global image, ref_points

    if not os.path.exists(image_path):
        logger.log_message(f"Image file not found: {image_path}", level='error')
        return None

    image = cv2.imread(image_path)
    if image is None:
        logger.log_message(f"Failed to read the image at: {image_path}", level='error')
        return None

    clone = image.copy()
    ref_points = []
    cv2.namedWindow("image")
    cv2.setMouseCallback("image", click_and_crop)

    logger.log_message(f"Please select the cropping coordinates on the image: {image_path}", level='info')

    while True:
        cv2.imshow("image", image)
        key = cv2.waitKey(1) & 0xFF
        if key == 8:  # Backspace key to reset
            image = clone.copy()
            ref_points = []
            logger.log_message(f"Resetting the selected cropping area.", level='info')

        elif key == 13:  # Enter key to accept
            logger.log_message(f"Cropping coordinates selected: {ref_points}.", level='info')
            break

    cv2.destroyAllWindows()

    if len(ref_points) == 2:
        return ref_points
    else:
        logger.log_message(f"No valid coordinates selected.", level='error')
        return None


def process_image(image_path, coords, conn, sddh_id):
    logger.log_message(f"Processing image: {image_path} with sddh_id: {sddh_id}.", level='info')
    image = cv2.imread(image_path)
    clone = image.copy()

    if image is None:
        logger.log_message(f"Image not found: {image_path}", level='error')
        return

    for i, (start, end) in enumerate(coords):
        roi = clone[start[1]:end[1], start[0]:end[0]]
        logger.log_message(f"Extracting text from ROI: {start} to {end}.", level='info')
        text = pytesseract.image_to_string(roi)

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        name = lines[0] if len(lines) > 0 else ""
        occupation = lines[1] if len(lines) > 1 else ""
        location = lines[2] if len(lines) > 2 else ""

        logger.log_message(f"OCR Result for {os.path.basename(image_path)}: Name: {name}, Occupation: {occupation}, Location: {location}.", level='info')

        if conn:
            save_to_db(conn, name, occupation, location, sddh_id)

def ocr_scrapping_save(root_folder):
    logger.log_message(f"Starting OCR scraping for root folder: {root_folder}", level='info')
    conn = DB.database_connection()  
    if not conn:
        logger.log_message("Failed to establish database connection. Exiting.", level='error')
        return
    try:
        
        selected_subfolder = os.listdir(root_folder)[0]
        selected_subfolder_path = os.path.join(root_folder, selected_subfolder)
        sddh_id = selected_subfolder
        logger.log_message(f"Selected subfolder: {selected_subfolder}, sddh_id: {sddh_id}", level='info')
        print(f"Selected sddh_id: {sddh_id}")

        before_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_before_scroll_page_1.png")
        after_scroll_image_path = os.path.join(selected_subfolder_path, f"{selected_subfolder}_after_scroll_page_1.png")

        logger.log_message(f"Selecting coordinates for 'before_scroll' image: {before_scroll_image_path}", level='info')
        print("Please select coordinates for the 'before_scroll' image:")
        coordinates_before_scroll = get_coordinates(before_scroll_image_path)

        logger.log_message(f"Selecting coordinates for 'after_scroll' image: {after_scroll_image_path}", level='info')
        print("Please select coordinates for the 'after_scroll' image:")
        coordinates_after_scroll = get_coordinates(after_scroll_image_path)

        if not coordinates_before_scroll or not coordinates_after_scroll:
            logger.log_message("Failed to get coordinates. Exiting.", level='error')
            return

        for subfolder in os.listdir(root_folder):
            subfolder_path = os.path.join(root_folder, subfolder)

            if not os.path.isdir(subfolder_path):
                logger.log_message(f"Skipping non-directory: {subfolder_path}", level='info')
                continue

            sddh_id = subfolder
            logger.log_message(f"Processing sddh_id: {sddh_id}", level='info')
            print(f"Processing sddh_id: {sddh_id}")
            
            page_number = 1
            while True:
                before_scroll_image = os.path.join(subfolder_path, f"{subfolder}_before_scroll_page_{page_number}.png")
                after_scroll_image = os.path.join(subfolder_path, f"{subfolder}_after_scroll_page_{page_number}.png")

                logger.log_message(f"Checking for page {page_number} images: {before_scroll_image}, {after_scroll_image}", level='info')

                if os.path.exists(before_scroll_image) and os.path.exists(after_scroll_image):
                    logger.log_message(f"Found both images for page {page_number}. Processing...", level='info')
                    process_image(before_scroll_image, [coordinates_before_scroll], conn,sddh_id)
                    process_image(after_scroll_image, [coordinates_after_scroll],conn, sddh_id)
                else:
                    logger.log_message(f"No more images found for page {page_number}. Stopping.", level='info')
                    break

                page_number += 1

    finally:
        if conn:
            conn.close()
            logger.log_message("Database connection closed.", level='info')