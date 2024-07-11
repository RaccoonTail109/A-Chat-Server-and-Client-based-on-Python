import socket
import threading
import datetime
import sys
import pickle
import uuid
import os
import warnings
warnings.filterwarnings('ignore')

class clientconnection:
    # create client socket
    def __init__(self,address):
        self.server_address = address
        self.socket_init()
        self.username=''
        self.activeuser_info={}
        self.expected_request_id = None

    # init TCP socket
    def socket_init(self):
        # create a TCP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect to the server
        self.server_socket.connect((self.server_address))

    # init UDP socket
    def udp_socket_init(self):
        self.udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # random allocate a port
        self.udp_server_socket.bind(('127.0.0.1',0 ))
        # *获取udp端口号
        # get the port number
        self.udp_port = self.udp_server_socket.getsockname()[1]
        # *开启接收线程
        # start the thread to receive video
        udp_listen_thread = threading.Thread(target=self.recv_video)
        udp_listen_thread.daemon = True
        udp_listen_thread.start()
        
    def generate_request_id(self):
        # create a unique request id for each request
        return uuid.uuid4().hex
    
    # send request to server
    def send_to_server(self,command,sender_username,**kwargs):
        request_id = self.generate_request_id()
        request_dict = {
            'request_id':request_id,
            'command':command,
            'sender_username':sender_username,
            'params':kwargs
        }
        send_data = pickle.dumps(request_dict)
        self.server_socket.send(send_data)
        return request_id
    
    # listen to server
    def recv_from_server(self):
        recv_data = self.server_socket.recv(1024)
        response = pickle.loads(recv_data)
        # print(f"Received response: {response}")  #! 调试语句
        return response
    
    # send video to target user
    def send_video(self,target_username,filename):
        if not os.path.exists(filename):
            print(f'File {filename} not exists.')
            return
        #* 获取目标用户的udp信息
        print(f"DEBUG: Starting to send video '{filename}' to user: {target_username}")#! 调试语句
        target_udp_info = self.get_target_udp_info(target_username)
        if not target_udp_info:
            print("DEBUG: Failed to get target UDP info.")  #! 调试语句
            return
        target_ip = target_udp_info['ip']
        target_port = target_udp_info['port']
        #*使用udp发送视频
        udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # *发送包含用户名和文件名的信息数据包
            info_data = f'info:{self.username}:{filename}'.encode()
            udp_client_socket.sendto(info_data, (target_ip, target_port))
            print(f"DEBUG: Sent file info data to {target_ip}:{target_port}")  # !调试语句
            with open(filename, 'rb') as f:
                while True:
                    bytes_read = f.read(1024)
                    if not bytes_read:
                        break
                    udp_client_socket.sendto(bytes_read, (target_ip, target_port))
                    print(f"DEBUG: Sent data packet to {target_ip}:{target_port}")  # !调试语句
        except Exception as e:
            print(f"ERROR: Exception in send_video: {e}")  #! 调试语句
            
        finally:
            udp_client_socket.close()
        print("Video file sent successfully.")

    # receive video from sender
    def recv_video(self):
        while True:
            # 接收数据包
            data, addr = self.udp_server_socket.recvfrom(1024)
            if not data:
                continue
            print(f"DEBUG: Received data packet from {addr}")  # !调试语句

            # *处理第一个数据包，它包含发送者的用户名和原始文件名
            if data.startswith(b'info:'):
                sender_info = data.decode().split(':')[1]  
                # *格式为 'info:Yoda:video.mp4'
                sender_username, original_filename = sender_info.split(':')
                filename = f'{sender_username}_{original_filename}'
                with open(filename, 'wb') as f:
                    while True:
                        data, _ = self.udp_server_socket.recvfrom(1024)
                        if not data or data.startswith(b'info:'):
                            break
                        else:
                            print(f"DEBUG: Data content: {data[:20]}")  # !调试语句
                        f.write(data)
                print(f'Received {original_filename} from {sender_username}.')
        

    # login
    def login(self):
        while True:
            username = input('username:')
            password = input('password:')
            #*在发送登录请求之前初始化udp socket
            # initialize udp socket before sending login request
            self.udp_socket_init()
            self.send_to_server('login', sender_username=username, username=username, password=password,udp_port=self.udp_port)
            login_response = self.recv_from_server()
            # print(f"Login response: Code: {login_response['code']}, Message: {login_response['message']}")  #! 调试语句
            if login_response['code'] == 0:
                self.username = username
                # print('login successfully.') #* 调试语句
                break
            else:
                print('login failed:',login_response['message'])

    # logout
    def logout(self):
        self.send_to_server('logout', sender_username=self.username)
        logout_response = self.recv_from_server()
        if logout_response['code'] == 0:
            self.username = ''
            print('logout successfully.')

        else:
            print('logout failed:',logout_response['message'])
    
    # receive message from server
    def recv_func(self):
        # print('线程开始' )#! 调试语句
        while True:
            try:
                # print("Waiting for server response...")  #! 调试信息
                response_dict = self.recv_from_server()
                # print(f"Received data: {response_dict}, Expected request ID: {self.expected_request_id}")  # !调试语句
                if 'request_id' in response_dict['request'] and response_dict['request']['request_id'] == self.expected_request_id:
                    command = response_dict['request']['command']
                    # print(f"Handling response for command: {command}")  #! 调试语句
                    if command == 'activeuser':
                        if response_dict['code'] == 0 and 'active_users' in response_dict:
                            for user_info in response_dict['active_users']:
                                username=user_info['username']
                                ip_address=user_info['ip_address']
                                port=user_info['port']
                                #* 将活跃用户信息存入字典
                                self.activeuser_info[username]={'ip_address':ip_address,'port':port}
                                print(f"{user_info['username']}, active since {user_info['timestamp']} at {user_info['ip_address']}; {user_info['port']}")
                        elif response_dict['code'] == -5:
                            print(response_dict['message'])
                        else:
                            print(f"Error in response: {response_dict}")
                    elif command == 'creategroup':
                        if response_dict["code"] == 0:
                            print("create group successfully")
                        elif response_dict["code"] == -8:
                            print(f"Group chat is already exist.")
                        elif response_dict["code"] == -9:
                            print(response_dict["message"]) 
                    elif command == 'msgto':
                        if response_dict["code"] == 0:
                            print("transmit successfully")
                        elif response_dict["code"] == -1:
                            print("No such user.")

                    elif command == 'joingroup':
                        if response_dict["code"] == 0:
                            print(response_dict["message"])
                        else:
                            print(response_dict["message"])
                    elif command == 'groupmsg':
                        if response_dict["code"] == 0:
                            print(response_dict["message"])
                        else:
                            print(response_dict["message"])
                    elif command == 'p2pvideo':
                        if response_dict["code"] == 0 and 'target_udp_info' in response_dict:
                            #*成功接收目标用户Udp信息
                            target_udp_info = response_dict['target_udp_info']
                            print(f'Debug: Received target UDP info: {target_udp_info}')  #! 调试语句
                        else:
                            print(f'Error in p2pvideo: {response_dict}')
                        
                    
                    self.expected_request_id = None
                elif 'transimit' in response_dict:
                    #* 说明是被转发的接收方
                    # means the receiver of the message
                    sender_username = response_dict["request"]["sender_username"]
                    message = response_dict["message"]
                    print(f"received from {sender_username}'s message: {message}")

                

                elif 'group_transimit' in response_dict:
                    #* 说明是被拉入群聊的接收方
                    # means the receiver of the group invitation
                    # print('Handling group transmission...')#! 调试语句
                    sender_username = response_dict["request"]["sender_username"]
                    message = response_dict["message"]
                    print(f'Received group invitation from {sender_username}: {message}')
                
                elif 'groupmsg_transimit' in response_dict:
                    #* 说明是群聊消息的接收方
                    #means the receiver of the group message
                    groupname = response_dict["request"]["params"]["groupname"]
                    sender_username = response_dict["request"]["sender_username"]
                    message = response_dict["message"]
                    print(f"Received group message from group {groupname}: {message}")
                    
                else:
                    # print(f"Ignoring unmatched response")
                    pass
            except Exception as e:
                # print(f"接收线程出现异常: {e}")  #! 调试语句
                break

    # handle activeuser command
    def handle_activeuser(self):
        try:
            #  print('sending activeuser request...') #! 调试语句
            request_id = self.send_to_server('activeuser', sender_username=self.username)
            # print(f"Expected request ID set to: {request_id}")  #! 调试语句
            self.expected_request_id = request_id
        except Exception as e:
            print(f"Error in handle_activeuser: {e}")
    
    # handle msgto command
    def handle_msgto(self, username, message):
        try:
            parts = message.split(' ', 2)  # 分割为最多三部分
            if len(parts) < 3:
                print("Invalid msgto command format.")
            command, username, message_content = parts
            request_id=self.send_to_server(command, sender_username=self.username, username=username, message=message_content)
            self.expected_request_id = request_id
        except Exception as e:
            print(f"Error in handle_msgto: {e}")
    
    # handle creategroup command
    def handle_creategroup(self, groupname,*usernames):
        try:
            request_id = self.send_to_server('creategroup', sender_username=self.username, groupname=groupname, members=list(usernames))
            self.expected_request_id = request_id
        except Exception as e:
            print(f"Error in handle_creategroup: {e}")

    # handle joingroup command
    def handle_joingroup(self, groupname):
        try:
            # print(f"Sending joingroup request for group: {groupname}") #! 调试语句
            request_id = self.send_to_server('joingroup', sender_username=self.username, groupname=groupname)
            # print(f"Expected request ID set to: {request_id}")  #! 调试语句
            self.expected_request_id = request_id
        except Exception as e:
            print(f"Error in handle_joingroup: {e}")

    # handle groupmsg command
    def handle_groupmsg(self, groupname, message):
        try:
            # print(f'sending groupmsg request for group: {groupname}') #! 调试语句
            request_id = self.send_to_server('groupmsg', sender_username=self.username, groupname=groupname,message=message)
            # print(f'groupmsg request sent, expected request ID set to: {request_id}')#! 调试语句
            self.expected_request_id = request_id
        except Exception as e:
            print(f"Error in handle_groupmsg: {e}")

    # get target user's udp info
    def get_target_udp_info(self,target_username):
        request_id= self.send_to_server('p2pvideo',sender_username=self.username,target_username=target_username)
        self.expected_request_id = request_id
        response_dict = self.recv_from_server()
        if response_dict['code'] == 0:
            return response_dict['target_udp_info']
        else:
            print('Error in get_target_udp_info:',response_dict['message'])
            return None

    # run socket
    def run_socket(self):
        recv_thread_start = False
        while True:
            if self.username == '':
                print('Please login')
                self.login()
                if not recv_thread_start:
                    # 成功登录后，开启接收线程
                    recv_thread = threading.Thread(target=self.recv_func)
                    recv_thread.daemon = True
                    recv_thread.start()
                    recv_thread_start = True
                    print('Welcome to TESSENGER!')
                    print('Enter one of following commands(msgto, activeuser, creategroup, joingroup, groupmsg, p2pvideo, logout)')
            else:
                message = input('[client]:')
                if message.startswith('logout'):
                    print(f'Bye, {self.username}!')
                    self.logout()
                    break
                elif message.startswith('msgto'):
                    self.handle_msgto(self.username, message)
                elif message.startswith('activeuser'):
                    self.handle_activeuser()
                elif message.startswith('creategroup'):
                    parts = message.split(' ')
                    if len(parts) < 2:
                        print("Invalid creategroup command format.")
                    else:
                        groupname = parts[1]
                        usernames = parts[2:]
                        self.handle_creategroup(groupname, *usernames)
                elif message.startswith('joingroup'):
                    parts = message.split(' ')
                    if len(parts) < 1:
                        print("Invalid joingroup command format.")
                    else:
                        groupname = parts[1]
                        self.handle_joingroup(groupname)
                elif message.startswith('groupmsg'):
                    parts = message.split(' ', 2)
                    if len(parts) < 3:
                        print("Invalid groupmsg command format.")
                    else:
                        groupname = parts[1]
                        message_content = parts[2]
                        self.handle_groupmsg(groupname, message_content)
                elif message.startswith('p2pvideo'):
                    parts = message.split(' ')
                    if len(parts) < 3:
                        print("Invalid p2pvideo command format.")
                    else:
                        target_username = parts[1]
                        filename = parts[2]
                        self.send_video(target_username, filename)

        self.server_socket.close()
        print('exit.')

# main function
if __name__ == '__main__':
    server_ip = sys.argv[1]
    port = int(sys.argv[2])
    client = clientconnection((server_ip,port))
    client.run_socket()
