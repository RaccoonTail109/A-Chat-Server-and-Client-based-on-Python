import socket
import threading
from datetime import datetime
import sys
import pickle

import warnings
warnings.filterwarnings('ignore')

# todo: 1. 成功登录和登出（已完成）
# todo: 2. 拉黑10s（已完成）
# todo: 3. mutiple clients（已完成）
# todo: 4. 用activeuser命令查看当前在线用户（已完成）
# todo: 5. 用msgto命令给其他用户发送消息（已完成）
# todo: 6. 用creategroup命令创建群组（已完成）
# todo: 7. 用joingroup命令加入群组（已完成）
"""
这里逻辑是群主即创建者先用creategroup命令指定加入的人，但如果指定的人没有用joingroup命令加入群，则它仍然收不到群消息也不能发送群消息
#! 查看这个测试例子
ref: https://edstem.org/au/courses/13756/discussion/1710652
"""
# todo: 8. 用groupmsg发送消息到群组（已完成）
# todo: 9. 显示转发和群组消息到命令行（已完成）
# todo: 10. report
# todo: 11. 代码注释
# todo: 12. UDP视频传输功能

"""
#todo:登录发送给服务器的请求格式：
{
request_id:request_id,
command: 'login',
sender_username: 'xxx',
params: {
    username: 'xxx',
    password: 'xxx',
    udp_port: 'xxx'}
}
#todo: 登录服务器返回的响应格式：
{
request: {
    request_id:request_id,
    command: 'login',
    sender_username: 'xxx',
    params: {
        username: 'xxx',
        password: 'xxx',
        udp_port: 'xxx'}
    },
code: 0,
message: 'ok'}
# todo:私聊消息sender发送给服务器的请求格式：
{
request_id:request_id,
command: 'msgto',
sender_username: 'sender',
params: {
    username: 'receiver',
    message: 'xxx',}
}
#todo:私聊消息服务器返回给sender的响应格式：
{
request: {
    request_id:request_id,
    command: 'msgto',
    sender_username: 'sender',
    params: {
        recv_username: 'receiver',
        message: 'xxx',}
    },
code: 0,
message: 'ok'}
#todo: 私聊消息服务器转发给receiver的响应格式：
{
request: {
    request_id:request_id,
    command: 'msgto',
    sender_username: 'sender',
    params: {
        recv_username: 'receiver',
        message: 'xxx',}
    },
transimit: True,
code: 0,
message: 'xxx'}
# todo: 使用activeuser命令查看当前在线用户的请求格式：
{
request_id:request_id,
command: 'activeuser',
sender_username: 'sender',
params: {}
}
# todo: 使用activeuser命令查看当前在线用户服务器的响应格式：
{
request: {
    request_id:request_id,
    command: 'activeuser',
    sender_username: 'sender',
    params: {}
    },
code: 0,
active_users: [
    {
    "username": "user1",
    "timestamp": "timestamp1",
    "ip_address": "ip1",
    "port": "port1"
    },
    {
    "username": "user2",
    "timestamp": "timestamp2",
    "ip_address": "ip2",
    "port": "port2"
    }]
}
#* 如果没有其他在线用户，则返回：
{
request: {
    request_id:request_id,
    command: 'activeuser',
    sender_username: 'sender',
    params: {}
    },
code: -5,
message: 'No other active user.'}
# todo: creategroup命令创建群组的请求格式：
{
request_id:request_id,
command: 'creategroup',
create_username: 'creator',
params: {
    groupname: 'xxx',
    members: ['user1','user2','user3']}
}
# todo: creategroup命令创建群组服务器返回群主的响应格式：
{
request: {
    request_id:request_id,
    command: 'creategroup',
    create_username: 'creator',
    params: {
        groupname: 'xxx',
        members: ['user1','user2','user3']}
    },
code: 0,
message: 'You have created the group successfully.'}
# todo: creategroup命令创建群组服务器返回群成员的响应格式：
{
request: {
    request_id:request_id,
    command: 'creategroup',
    create_username: 'creator',
    params: {
        groupname: 'xxx',
        members: ['user1','user2','user3']}
    },
    group_transimit: True,
    code: 0,
    message: 'You have been invited to the group.'}
# todo: joingroup命令加入群组的请求格式：
{
request_id:request_id,
command: 'joingroup',
sender_username: 'sender',
params: {
    groupname: 'xxx'}
}
# todo: joingroup命令加入群组服务器返回的响应格式：
{
request: {
    request_id:request_id,
    command: 'joingroup',
    sender_username: 'sender',
    params: {
        groupname: 'xxx'}
    },
code: code,
message: message}
# todo: groupmsg命令发送群消息的请求格式：
{
request_id:request_id,
command: 'groupmsg',
sender_username: 'sender',
params: {
    groupname: 'xxx',
    message: 'xxx'}
}
# todo: groupmsg命令发送群消息服务器返回发送人的响应格式：
{
request: {
    request_id:request_id,
    command: 'groupmsg',
    sender_username: 'sender',
    params: {
        groupname: 'xxx',
        message: 'xxx'}
    },
    code: code,
    message: message}
# todo: groupmsg命令发送群消息服务器返回群成员的响应格式：
{
request: {
    request_id:request_id,
    command: 'groupmsg',
    sender_username: 'sender',
    params: {
        groupname: 'xxx',
        message: 'xxx'}
    },
    groupmsg_transimit: True,
    code: code,
    message: message}
# todo: p2p视频传输的请求获取发送方udp端口的格式：
{
request_id:request_id,
command: 'p2pvideo',
sender_username: 'sender_username',
params: {
    target_username: 'target_username',
    filename: 'filename'}
    }
}
# todo: p2p视频传输的请求获取发送方udp端口的响应格式：
{
request: {
    request_id:request_id,
    command: 'p2pvideo',
    sender_username: 'sender_username',
    params: {
        target_username: 'target_username',
        filename: 'filename'}
        },
    code: code,
    message: message,
    target_udp_info: {
        'ip_address': 'xxx',
        'udp_port': 'xxx'
    }
"""   
class base_logger():
    # create a base logger class
    def __init__(self, filename):
        self.filename = filename
        self.filecontent = open(self.filename, 'a')

    # write log to file
    def write_log(self, filetext):
        try:
            self.filecontent.write(filetext + '\n')
            self.filecontent.flush()
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def close(self):
        self.filecontent.close()

class user_logger(base_logger):
    # create a user logger class
    def __init__(self, filename:str):
        super().__init__(filename)
        self.index = 0
    # write userlog to file
    def write_userlog(self, username:str, sender_ip:str, sender_port: int):
        self.index += 1
        self.username = username
        self.client_ip = sender_ip
        self.client_port = str(sender_port)
        now = datetime.now()
        cur_datetime = now.strftime('%d %b %Y %H:%M:%S')
        log_text = [str(self.index), cur_datetime, self.username, self.client_ip, self.client_port]
        self.filecontent.write('; '.join(log_text) + '\n')
        self.filecontent.flush()

class message_logger(base_logger):
    # create a message logger class
    def __init__(self, filename):
        super().__init__(filename)
        self.index = 0
    # write message log to file
    def write_msglog(self,sender:str,*args):
        self.index += 1
        self.sender = sender
        now = datetime.now()
        cur_datetime = now.strftime('%d %b %Y %H:%M:%S')
        log_text = [str(self.index), cur_datetime, self.sender] + list(args)
        self.filecontent.write('; '.join(log_text) + '\n')
        self.filecontent.flush()

class group_logger(base_logger):
    # create a group logger class
    def __init__(self, groupname):
        filename = f'{groupname}_messageLog.txt'
        super().__init__(filename)
        self.index = 0
    # write group log to file
    def write_grouplog(self, sender:str, message:str):
        self.index += 1
        self.sender = sender
        now = datetime.now()
        cur_datetime = now.strftime('%d %b %Y %H:%M:%S')
        log_text = [str(self.index), cur_datetime, self.sender, message]
        self.filecontent.write('; '.join(log_text) + '\n')
        self.filecontent.flush()

class User:
# 管理单个用户的登录登出拉黑解除拉黑
# manage the login, logout, block and unblock of a single user
    def __init__(self,username:str,password:str):
        self.username = username
        self.password = password
        self.login_status = 'logout'
        self.block_status = 0
        #socket是一个套接字对象，当登录后用来发送和接收数据
        self.socket = None
        self.address = tuple()
    
    # unblock the user
    def unblock(self):
        self.block_status = 0
        # print( 'You have been unblocked.')
    # recover the user after 10s
    def recover_block(self):
        timer = threading.Timer(10,self.unblock)
        # after 10s, execute unblock function
        #在10s后执行unblock函数
        timer.start()

    # login
    def login(self,password:str, max_retry_times:int,socket,address,user_logger):
        if self.login_status == 'login':
            return False,-1,'You have already logged in.'
        #if the user has been blocked, return false
        if self.block_status >= max_retry_times:
            # print( f'{self.username} have been blocked for 10s.')
            self.recover_block()
            return False,-4,'Your account have been blocked due to multiple login failures. Please try again later'
        #if the password is wrong, return false
        if password != self.password:
            self.block_status += 1
            return False,-2,'Invalid Password. Please try again'
        #if the user has not been blocked and the password is correct, login successfully
        self.login_status = 'login'
        self.socket = socket
        self.address = address
        #! 注意这里的user_logger是一个实例，不是类，这里不能用下面一行的代码创建一个性的实例而是使用这个实例
        #! user_log = user_logger('user_log.txt')
        user_logger.write_userlog(self.username,str(address[0]),str(address[1]))
        return True,0,'Login successfully.'
    
    # logout
    def logout(self):
        if self.login_status != 'login':
            return False,-1,'You have not logged in.'
        self.login_status = 'logout'
        self.socket = None
        self.address = tuple()
        return True,0,'Logout successfully.'

class Group:
    # manage the single group chat
    def __init__(self,groupname,creator):
        self.groupname = groupname
        # to store the group members, creator is the first member
        #* 用来储存群组成员，creator是群主也是第一个成员
        self.creator = creator
        self.members = {creator}
        self.invited_set = set()
        # to store the users who have been invited but not joined
        #* 用来储存已经被邀请但还没有加入的用户
        self.logger = group_logger(groupname)

    # invite users to join the group
    def invite_users(self, *usernames):
        #* 向invited_set中添加用户
        self.invited_set.update(usernames)
        return True, 0, 'You have created the group successfully.'

    # join the group
    def joingroup(self,username:str):
        #* 如果用户在invited_set中且不在members中，则将其加入members中（被邀请但没确认）
        if username in self.invited_set and username not in self.members:
            self.members.add(username)
            self.invited_set.remove(username)
            return True, 0 , 'You have joined the group successfully.'
        elif username in self.members:
            return False, -6, 'You have already joined the group.'
        else:
            return False, -7, 'You have not been invited to join the group.'
        
class GroupManager:
    #* 管理所有群组的信息
    # manage all the groups
    def __init__(self,users_manager):
        #* 用来储存所有群组的字典，key是群组名，value是Group类的实例
        self.group_list = {}
        self.users_manager = users_manager

    # get all the members in the group
    def get_usernames(self,groupname):
        #* 返回群组中所有成员的用户名
        return ' '.join(self.group_list[groupname].members)
    
    # create a group
    def create_group(self,groupname,creator, usernames):
        if groupname in self.group_list:
            return False,-8,f"a group chat (Name: {groupname} already exist.)"
        
        active_users = self.users_manager.get_all_activeuser()
        # check if all the invited users are online
        #* 检查所有被邀请的用户是否在线
        for uname in usernames:
            # if the user is not online, return false
            if uname not in active_users:
                return False,-9,f"User {uname} is not online."
        #create a new group instance and add it to group_list
        #* 创建group实例并将其加入group_list
        new_group = Group(groupname,creator)
        new_group.invite_users(*usernames)
        self.group_list[groupname] = new_group
        return True,0,f"Group chat room has been created, room name: {groupname}, users in this room: {self.get_usernames(groupname)}"
    
    # join a group
    def join_group(self,groupname,username):
        # if the group does not exist, return false
        if groupname not in self.group_list:
            return False,-10,f"Group chat (Name: {groupname}) does not exist."
        #*从group_list中取出group实例
        group = self.group_list[groupname]
        return group.joingroup(username)


class UsersManager:
    # manage all the users
    #*管理所有用户的登录登出
    def __init__(self,max_retry_times:int):
        self.data_file = 'credentials.txt'
        self.status_file = 'user_log.txt'
        self.user_list = dict()
        self.users_init()
        self.max_retry_times = max_retry_times
        self.active_udp_users = {}

    # read the user information from the file
    def users_init(self):
        with open(self.data_file,'r') as f:
            for line in f.readlines():
                username,password = line.split()
                self.user_list[username] = User(username,password)

    # login
    def log_in(self,username,password, socket, address,user_logger,udp_port):
        if username in self.user_list:
            login_success,code,message =self.user_list[username].login(password, self.max_retry_times,socket, address,user_logger)
            if login_success:
                self.active_udp_users[username] = {'ip': address[0], 'udp_port': udp_port}
            return login_success,code,message
        else:
            return False,-3,'No such user.'
    
    # logout
    def log_out(self,username):
        if username in self.user_list:
            return self.user_list[username].logout()
        else:
            return False,-3,'No such user.'
    
    # get active users except the current user
    def activeuser(self,current_username):
        active_user_list = []
        with open(self.status_file,'r') as f:
            for line in f.readlines():
                index,timestamp, username,user_ip, user_port = line.split('; ')
                if username != current_username:
                    user_info = {
                        'username': username,
                        'timestamp': timestamp,
                        'ip_address': user_ip,
                        'port': user_port
                    }
                    active_user_list.append(user_info)
        return active_user_list
    
    # get all the active users
    def get_all_activeuser(self):
        active_user_set = set()
        with open(self.status_file,'r') as f:
            for line in f.readlines():
                _,_, username,_, _ = line.split('; ')
                active_user_set.add(username)
        return active_user_set
    
    # get the socket of the user
    def get_socket(self,username):
        if username in self.user_list:
            return self.user_list[username].socket
        else:
            return None
    
    # get the udp info of the user
    def get_udp_info(self,username):
        return self.active_udp_users.get(username)

        


class serverTCPconnection:
    # TCP connection
    def __init__(self,  port:int, max_retry_times:int):
        self.address = ('127.0.0.1' ,port)
        self.max_retry_times = max_retry_times
        self.socket_init()

        #*初始化用户管理器
        # Initialize the user manager
        self.users_manager = UsersManager(max_retry_times)

        #*初始化群组管理器并传入用户实例
        # Initialize the group manager and pass in the user instance
        self.group_manager = GroupManager(self.users_manager)

        #*初始化日志记录器
        # Initialize the loggers
        self.user_logger = user_logger('user_log.txt')
        self.message_logger = message_logger('message_log.txt')

    def socket_init(self):
        # create a TCP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(self.address)

    # send data to client
    def send_to_client(self,client_socket,response):
        try:
            send_data = pickle.dumps(response)
            client_socket.send(send_data)
            # print('Sent data to client: {}'.format(response))  #! 调试语句
        except Exception as e:
            ## print('Error sending data to client: {}'.format(e))  #! 调试语句
            pass
    
    # listen to the client
    def recv_from_client(self,client_socket):
        recv_data = client_socket.recv(1024)
        request_dict = pickle.loads(recv_data)
        return request_dict

    # accept connections
    def accept_connections(self):
        #* 监听端口，等待客户端连接
        #* 为每个新连接创建线程来处理，传入handle_client方法
        self.server_socket.listen()
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"accepted new connection from{client_address}")
            client_thread = threading.Thread(target=self.handle_client,args=(client_socket,client_address))
            client_thread.daemon = True
            client_thread.start()

    # handle the client command
    def handle_client(self,client_socket,client_address):
        while True:
            try:
                request_dict = self.recv_from_client(client_socket)
                # print(f"Received request: Command: {request_dict['command']}, Username: {request_dict['sender_username']}, Params: {request_dict['params']}")  #!调试语句
                print(f"DEBUG: Received request: {request_dict}")  #! 调试语句

                command = request_dict['command']
                sender_username = request_dict['sender_username']
                params = request_dict['params']
                
                # if the command is login, get the udp port
                if command == 'login':
                    udp_port = params.get('udp_port')
                    if_success,code,message= self.users_manager.log_in(sender_username, params['password'], client_socket, client_address,self.user_logger,udp_port)
                    # print(f"Login attempt: {if_success}, Code: {code}, Message: {message}")  #! 调试语句
                    # construct the response dictionary
                    response_dict = {
                        'request': request_dict,
                        'code': code,
                        'message': message
                    }
                    # send the response to the client
                    self.send_to_client(client_socket, response_dict)
                # if the command is logout, log out the user
                elif command == 'logout':
                    if_success, code, message = self.users_manager.log_out(sender_username)
                    # print(f"Logout attempt: {if_success}, Code: {code}, Message: {message}")  #! 调试语句
                    # construct the response dictionary
                    response_dict = {
                    "request": request_dict,
                    "code": code,
                    "message": message}
                    # send the response to the client
                    self.send_to_client(client_socket, response_dict)
                # if the command is activeuser, get the active users 
                elif command == 'activeuser':
                    # print('precessing activeuser command') #! 调试语句
                    active_user = self.users_manager.activeuser(sender_username)
                    # print(f"Active user: {active_user}")  #! 调试语句
                    # construct the response dictionary
                    if active_user:
                        response_dict = {
                        "request": request_dict,
                        "code": 0,
                        "active_users": active_user}
                    else:
                        response_dict = {
                            "request": request_dict,
                            "code": -5,
                            "message": 'No other active user.'}
                    # send the response to the client 
                    self.send_to_client(client_socket, response_dict)
                    # print('Sent activeuser response: {}'.format(response_dict))  #! 调试语句
                # if the command is msgto, send the message to the target user
                elif command == 'msgto':
                    target_username = params['username']
                    message = params['message']
                    # get the socket of the target user
                    target_socket = self.users_manager.get_socket(target_username)
                    if target_socket:
                        # construct the response dictionary to the target user
                        #* 构造发送给目标用户的响应字典
                        target_response_dict = {
                        "request": request_dict,
                        "transimit": True,
                        "code": 0,
                        "message": message
                    }
                        # send the message to the target user
                        self.send_to_client(target_socket, target_response_dict)
                        # record the message to the message log
                        #* 记录消息日志
                        self.message_logger.write_msglog(sender_username,message)
                        # construct the response dictionary to the sender
                        #* 构造发送给发送者的响应字典
                        sender_response_dict = {
                        "request": request_dict,
                        "code": 0,
                        "message": 'ok'}
                        # send the response to the sender
                        self.send_to_client(client_socket, sender_response_dict)
                    else:
                        response_dict = {
                        "request": request_dict,
                        "code": -1,
                        "message": 'No such user.'
                    }
                    # send the response to the sender
                    self.send_to_client(client_socket, response_dict)
                # if the command is creategroup, create a group
                elif command == 'creategroup':
                    groupname = params['groupname']
                    creator = sender_username
                    members = params['members']
                    # 创建群组并返回相应的响应
                    create_success, create_code, create_message = self.group_manager.create_group(groupname, sender_username, members)
                    # construct the response dictionary to the creator
                    response_dict_creator = {
                        "request": request_dict,
                        "code": create_code,
                        "message": create_message
                    }
                    # send the response to the creator
                    self.send_to_client(client_socket, response_dict_creator)
                    if create_success:
                        # construct the response dictionary to the members
                        response_dict_members = {
                            "request": request_dict,
                            "group_transimit": True,
                            "code": 0,
                            "message": f"You have been invited to the group {groupname}."
                        }
                        # send the response to all members
                        for member in members:
                            if member != sender_username:
                                member_socket = self.users_manager.get_socket(member)
                                if member_socket:
                                    self.send_to_client(member_socket, response_dict_members)
                # if the command is joingroup, join a group
                elif command == 'joingroup':
                    groupname = params['groupname']
                    # print(f"Processing joingroup command, request ID from client: {request_dict['request_id']}")# !调试语句
                    # if the group does not exist, return false
                    if groupname in self.group_manager.group_list:
                        group = self.group_manager.group_list[groupname]
                        join_success, join_code, join_message = self.group_manager.join_group(groupname, sender_username)
                        # construct the response dictionary
                        response_dict = {
                            "request": request_dict,
                            "code": join_code,
                            "message": join_message
                        }
                        # send the response to the client
                        self.send_to_client(client_socket, response_dict)
                        # print(f"Sent joingroup response to client, request ID: {response_dict['request']['request_id']}")#! 调试语句
                # if the command is groupmsg, send the message to the group
                elif command == 'groupmsg':
                    groupname = params['groupname']
                    message = params['message']

                    # *检查群组是否存在
                    # check if the group exists
                    if groupname not in self.group_manager.group_list:
                        # print(f"Group {groupname} exists: {groupname in self.group_manager.group_list}")#! 调试语句
                        # construct the response dictionary to the sender
                        response_dict = {
                            "request": request_dict,
                            "code": -10,
                            "message": f"Group chat (Name: {groupname}) does not exist."
                        }
                        # print(f"Sending -10 response to sender: {response_dict}")  #! 调试语句
                        # send the response to the sender
                        self.send_to_client(client_socket, response_dict)
                        # print(f"Sent response to sender: {response_dict}")  #! 调试语句
                    group = self.group_manager.group_list[groupname]
                    # *检查发送者是否在群组中
                    # check if the sender is in the group
                    if sender_username not in group.members:
                        # print(f"Sender {sender_username} is in group: {sender_username in group.members}")#! 调试语句
                        # construct the response dictionary to the sender
                        response_dict = {
                            "request": request_dict,
                            "code": -11,
                            "message": f"You have not joined the group {groupname}."
                        }
                        # send the response to the sender
                        # print(f"Sending -11 response to sender: {response_dict}")#! 调试语句
                        self.send_to_client(client_socket, response_dict)
                        # print(f"Sent -11 response to sender: {response_dict}")#! 调试语句
                    # *记录到组消息日志
                    # record the message to the group message log
                    group.logger.write_grouplog(sender_username,message)
                    # print('recorded group message to log')#! 调试语句
                    # construct the response dictionary to the sender
                    sender_response_dict = {
                        "request": request_dict,
                        "code": 0,
                        "message": 'message sent successfully.'
                    }
                    # send the response to the sender
                    # print(f"Sending 0 response to sender: {sender_response_dict}")#! 调试语句
                    self.send_to_client(client_socket, sender_response_dict)
                    # print(f"Sent 0 response to sender: {sender_response_dict}")#! 调试语句

                    #*转发消息到群组中的其他成员
                    # transmit the message to other members in the group
                    for member in group.members:
                        # don't send the message to the sender
                        if member !=sender_username:
                            member_socket = self.users_manager.get_socket(member)
                            if member_socket:
                                forword_response_dict = {
                                    "request": request_dict,
                                    "groupmsg_transimit": True,
                                    "code": 0,
                                    "message": f'{sender_username}: {message}'
                                }
                                # print(f"Sending group message to member {member}: {forword_response_dict}")#! 调试语句
                                # send the message to the member
                                self.send_to_client(member_socket, forword_response_dict)
                                # print(f"Sent group message to member {member}: {forword_response_dict}") #! 调试语句
                # if the command is p2pvideo, send the udp info of the sender to the target user
                elif command == 'p2pvideo':
                    target_username = params['target_username']
                    print(f"DEBUG: Handling p2pvideo request for target user: {target_username}")  #! 调试语句
                    # check if the target user is online
                    if target_username not in self.users_manager.active_udp_users:
                        response_dict = {
                            'request':request_dict,
                            'code': -1,
                            'message': f'{target_username} is not online.'}
                    else: 
                        #*获取目标用户的udp信息
                        target_udp_info = self.users_manager.get_udp_info(target_username)
                        response_dict={
                            'request':request_dict,
                            'code': 0,
                            'message': 'UDP info sent successfully.',
                            'target_udp_info': target_udp_info}
                    # send the response to the sender
                    self.send_to_client(client_socket, response_dict)

            except Exception as e:
                print(f"ERROR: Exception in handle_client: {e}")  # !调试语句
                break
        # close the socket
        client_socket.close()
        print(f"connection with {client_address} closed")
        self.user_logger.close()
        self.message_logger.close()

if __name__ == '__main__':
    # run the server
    port = int(sys.argv[1])
    max_retry_times = int(sys.argv[2])
    server = serverTCPconnection(port,max_retry_times)
    server.accept_connections()