# -*- coding: utf-8 -*-

import re

from Transfer.baidu_fanyi import Transfer
from basic.get import *
from basic.task import *
from multithread.threads import *
from apibase.ChatGPTAPI import Chatbot

# data
global_thread = []


def debug_switch():
    qs = {
        "id": getid(),
        "type": DEBUG_SWITCH,
        "content": "off",
        "wxid": "",
    }
    s = json.dumps(qs)
    return s


def handle_nick(j):
    data = json.loads(j["content"])
    print("测试群成员昵称：" + data["nick"])
    return data["nick"]


def hanle_memberlist(j):
    data = j["content"]
    print(data)
    # for d in data:
    #     print(d["room_id"])


def destroy_all():
    qs = {
        "id": getid(),
        "type": DESTROY_ALL,
        "content": "none",
        "wxid": "node",
    }
    s = json.dumps(qs)
    return s


def handle_wxuser_list(j):
    content = j["content"]
    i = 0
    # 微信群
    for item in content:
        i += 1
        id = item["wxid"]
        m = id.find("@")
        if m != -1:
            print(i, "群聊", id, item["name"])

    # 微信其他好友，公众号等
    for item in content:
        i += 1
        id = item["wxid"]
        m = id.find("@")
        if m == -1:
            print(i, "个体", id, item["name"], item["wxcode"])


def handle_recv_txt_msg(j):
    print(j)

    wx_id = j["wxid"]
    room_id = ""
    content: str = j["content"].strip()

    access_internet: bool = False
    is_room: bool
    chatbot: Chatbot

    if len(wx_id) < 9 or wx_id[-9] != "@":
        is_room = False
        wx_id: str = j["wxid"]
        chatbot = global_dict.get((wx_id, ""))

    else:
        is_room = True
        wx_id = j["id1"]
        room_id = j["wxid"]
        chatbot = global_dict.get((wx_id, room_id))

    is_citation = (grpCitationMode and is_room) or (prvCitationMode and not is_room)

    print("isRoom:" + str(is_room))

    if autoReply and ((not is_room and prvReplyMode) or (is_room and grpReplyMode)):
        if content.startswith(helpKey):
            reply = '我是一个基于ChatGPT的聊天机器人，你可以@我聊天，也可以支持以下命令  \n' + helpKey + " 查看可用命令帮助\n" + \
                    ((groupImgKey + " 输入关键词画图，关键词用空格分开 ") if is_room else (
                            privateImgKey + " 输入关键词画图，关键词用空格分开 ")) + \
                    negativePromptKey + " 可选负面提示\n" + \
                    ((groupChatKey + " 提问群聊天机器人 ") if is_room else (privateChatKey + " 提问聊天机器人 ")) + \
                    internetKey + " 可联网\n" + \
                    resetChatKey + " 重置上下文\n" + \
                    regenerateKey + " 重新生成答案\n" + \
                    rollbackKey + " +数字n 回滚到倒数第n个问题\n" + \
                    characterKey + " 更改机器人角色设定\n" + \
                    conclusionKey + " 总结对话"

            nm = NormalTask(ws, content, reply, wx_id, room_id, is_room, False)
            nrm_que.put(nm)

        elif content.startswith(resetChatKey):
            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "rs")
            chat_que.put(ct)

        elif content.startswith(regenerateKey):
            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "rg")
            chat_que.put(ct)

        elif content.startswith(rollbackKey):
            if chatbot is None or chatbot.question_num == 0:
                reply = "您还没有问过问题"

            else:
                num = re.sub("^" + rollbackKey, "", content, 1).lstrip()
                if num.isdigit():
                    if chatbot.question_num < int(num):
                        reply = "无法回滚到" + num + "个问题之前"

                    else:
                        chatbot.rollback_conversation(int(num))
                        reply = "已回滚到" + num + "个问题之前"
                else:
                    reply = "请在回滚指令后输入有效数字"

            nm = NormalTask(ws, content, reply, wx_id, room_id, is_room, is_citation)
            nrm_que.put(nm)

        elif content.startswith(characterKey):
            content = re.sub("^" + characterKey, "", content, 1).lstrip()
            if chatbot is None:
                chatbot = Chatbot(
                    api_config,
                )
                if is_room:
                    global_dict[(wx_id, room_id)] = chatbot
                else:
                    global_dict[(wx_id, "")] = chatbot

            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "p")
            chat_que.put(ct)

        elif content.startswith(conclusionKey):
            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "z")
            chat_que.put(ct)

        elif stableDiffRly and (
                (content.startswith(privateImgKey) and not is_room) or (content.startswith(groupImgKey) and is_room)):
            content = re.sub("^" + (groupImgKey if is_room else privateImgKey), "", content, 1).lstrip()
            print("图片关键字：" + content)
            content = Transfer().transferTxt(content)
            prompt_list = re.split(negativePromptKey, content)

            ig = ImgTask(ws, prompt_list, wx_id, room_id, is_room, "2.1")
            img_que.put(ig)

        elif (content.startswith(privateChatKey) and not is_room) or (
                content.startswith(groupChatKey) and is_room) or content.startswith("@此号已注销"):
            content = re.sub("^" + (groupChatKey if is_room else privateChatKey), "",
                             content, 1).lstrip()
            if content.startswith(internetKey):
                content = re.sub("^" + internetKey, "", content, 1).lstrip()
                access_internet = True
            if chatbot is None:
                chatbot = Chatbot(
                    api_config,
                )
                if is_room:
                    global_dict[(wx_id, room_id)] = chatbot
                else:
                    global_dict[(wx_id, "")] = chatbot

            ct = ChatTask(ws, content, access_internet, chatbot, wx_id, room_id, is_room, is_citation, "c")
            chat_que.put(ct)


def handle_recv_pic_msg(j):
    print(j)


def handle_recv_txt_cite(j):
    pass


def handle_heartbeat(j):
    pass


def on_open(ws):
    # chatbot = Chatbot(
    #     rev_config,
    #     conversation_id=None,
    #     parent_id=None,
    # )
    # try:
    #     chatbot.login()
    # except Exception:
    #     raise Exception("Exception detected, check revChatGPT login config")
    # else:
    #     print("\nChatGPT login test success!\n")

    # ws.send(send_pic_msg(wx_id="filehelper", room_id="", content=""))
    # ws.send(send_wxuser_list())
    # ws.send(get_chatroom_memberlist())

    # ws.send(send_txt_msg("server is online", "filehelper"))
    # ws.send(send_pic_msg(wx_id="filehelper", content=os.path.join(os.path.abspath(cache_dir), "")))
    ws.send(get_personal_info())

    for i in range(0, 4):
        normal_processor = Processor(nrm_que)
        global_thread.append(normal_processor)

    for i in range(0, 2):
        chat_processor = Processor(chat_que)
        global_thread.append(chat_processor)

    for i in range(0, 4):
        image_processor = Processor(img_que)
        global_thread.append(image_processor)


def on_message(ws, message):
    j = json.loads(message)
    # print(j)

    resp_type = j["type"]

    # switch
    action = {
        HEART_BEAT: handle_heartbeat,
        RECV_TXT_MSG: handle_recv_txt_msg,
        RECV_PIC_MSG: handle_recv_pic_msg,
        NEW_FRIEND_REQUEST: print,
        RECV_TXT_CITE_MSG: handle_recv_txt_cite,

        TXT_MSG: print,
        PIC_MSG: print,
        AT_MSG: print,

        USER_LIST: handle_wxuser_list,
        GET_USER_LIST_SUCCESS: handle_wxuser_list,
        GET_USER_LIST_FAIL: handle_wxuser_list,
        ATTACH_FILE: print,

        CHATROOM_MEMBER: hanle_memberlist,
        CHATROOM_MEMBER_NICK: handle_nick,
        DEBUG_SWITCH: print,
        PERSONAL_INFO: print,
        PERSONAL_DETAIL: print,
    }

    action.get(resp_type, print)(j)


def on_error(ws, error):
    print(ws)
    print(error)


def on_close(ws):
    for key, value in global_dict.items():
        print("clear conversation:" + key)
        del value

    print(ws)
    print("closed")


server = "ws://" + server_host

# websocket.enableTrace(True)

ws = websocket.WebSocketApp(server,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
