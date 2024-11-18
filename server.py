import os
import socket
import threading
import queue
from message import  Message




PORT = 5050  # port xác định cho server
FORMAT = "utf-8"
MESSAGE_SIZE = 1024
SERVER_DATA_PATH ="C:\Users\letru\OneDrive\Desktop\MMT\Đồ án Socket"
CLIENT_UPLOAD_PATH = "C:\Users\letru\OneDrive\Desktop\MMT\Đồ án Socket"

connections =[]


SERVER = socket.gethostbyname(socket.gethostname())  # ip local
sever = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sever.bind((SERVER, PORT))  # bind server với port



def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))  # Bind tới địa chỉ bất kỳ và cổng 0
        port = s.getsockname()[1]  # Lấy cổng đã được cấp phát
        return port




def send_file (file_name, conn):
    file = open(file_name, "rb")
    file_size = os.path.getsize(file)


    data = file.read()

        # chia nhỏ dữ liệu và gửi đi
   
    file.close()

def receive_file (file_name,conn):
    pass




def handle_download (download_conn, download_tasks):
    while not download_tasks.empty():
        file_name = download_tasks.queue[0];
        send_file (file_name, download_conn)
        download_tasks.get()




def handle_upload (upload_conn, upload_tasks):
    while not upload_tasks.empty():
        file_name = upload_tasks.queue[0]
        receive_file (file_name,upload_conn)
        upload_tasks.get()



def control_connection(conn, addr):
    conn.settimeout(300)
    print(f"[NEW CONNECTION] {addr} connected")
    try:
        #kiểm tra mã PIN xác thực
        # clinet_login (conn, addr)
        # send wellcome (health message)

        # generate 2 port, tạo 2 socket mới
        upload_port = find_free_port()
        upload = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        download_port = find_free_port()
        download = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # gửi đăng nhập thành công cùng 2 port upload và download cho client để connect
        # chờ kết nối
        upload.listen(1)
        upload_conn, upload_addr = upload.accept()
        download.listen(1)
        download_conn, donwnload_addr = download.accept()

        # Tạo thread để xử lý upload và download, client cũng sẽ tạo thread tương ứng
        upload_thread = threading.Thread(target=handle_upload,
                                         args=(upload_conn, addr, upload_tasks))
        upload_thread.daemon = True

        download_thread = threading.Thread(target=handle_download,
                                           args=(download_conn, addr, download_tasks))
        download_thread.daemon = True
        
        connected = True
        upload_tasks = queue.Queue()
        download_tasks = queue.Queue()


        while connected:
            conn.settimeout(300)
            message = Message.receive_message(conn).decode(FORMAT)
            if not message :
                connected = False
                print(f"[{addr}] connection lost")
                break

            message = Message.extract_json(message)

            if message ["type"] == Message.DISCONNECT:
                connected = False
                print (f"[{addr}] {Message.DISCONNECT}")
                break

            elif message["type"] == Message.GET_RESOURCES:
                pass

            elif message["type"] == Message.UPLOAD_REQUEST:
                upload_tasks.put(message["data"]["filename"])
                if not upload_thread.is_alive():
                    upload_thread.start

            elif message["type"] == Message.DOWNLOAD_REQUEST:
                file_name = message["data"]["filename"]
                # kiểm tra file_name là đường hay tên file
                found_file = os.path.exists(
                    os.path.join(SERVER_DATA_PATH,message["data"]["filename"])
                )
                # gửi response

                if found_file:
                    download_tasks.put(file_name)
                    if not download_thread.is_alive():
                        download_thread.start()
            else :
                print(f"[{addr}] Unknown message type: {message['type']}")
                # response lỗi

    except (ConnectionError, socket.timeout):
        # Xử lý khi mất kết nối hoặc timeout
        connected = False
        print(f"[LOST CONNECTON] with {addr} ")

    
    upload_thread.join()
    download_thread.join()
    upload.close()
    download.close()
    conn.close()  # Đóng kết nối socket khỏi hệ thống
    connections.remove(conn)  # Loại bỏ kết nối khỏi danh sách connections



def main ():
    print("[STARTING] Server is online")
    sever.listen()
    try:
        while True:
            conn, addr = sever.accept()
            # conn là socket mới được tạo ra để giao tiếp với client
            # addr là địa chỉ của client

            connections.append(conn)
            conn_thread = threading.Thread(target=control_connection,
                                           args=(conn, addr))
            conn_thread.daemon = True  # kill thread khi hàm main kết thúc
            # tránh việc các thread chặn chương trình nếu try không thành công
            conn_thread.start()



    except KeyboardInterrupt:  # thêm các lỗi khác nếu cần
        print("[ERROR] Server shutting down")

    finally:
        for conn in connections:
            conn.close()
        sever.close()


if __name__ == "__main__":
    main ()

# thư viện pickel để chuyển object thành byte
# deamon thread sẽ tự động kết thúc khi main thread kết thúc




# # Server xử lý song song
# def handle_upload_request(client_socket, request):
#     filename = request['data']['filename']
#     file_type = request['data']['type']

#     def upload_item(item):
#         # Xử lý upload cho từng item
#         save_file(item)

#     if file_type == "file":
#         # Nếu là file, xử lý upload ngay
#         upload_item(filename)
#     else:
#         # Nếu là folder, tạo thread cho từng item trong folder
#         threads = []
#         folder_items = get_folder_items(filename)
#         for item in folder_items:
#             thread = threading.Thread(target=upload_item, args=(item,))
#             threads.append(thread)
#             thread.start()

#         # Đợi các thread hoàn thành
#         for thread in threads:
#             thread.join()

#     # Gửi phản hồi upload
#     response = {
#         "type": "UPLOAD_RESPONSE",
#         "data": {
#             "status": "success",
#             "message": "Upload complete"
#         }
#     }
#     client_socket.send(response)
