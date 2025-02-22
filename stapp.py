import os
from dotenv import load_dotenv

import json
import openai

import streamlit as st

GPT_MODEL = "ep-20250221122502-sg9dj"

# 获取环境变量
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY,base_url = "https://ark.cn-beijing.volces.com/api/v3")

tools = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email to the specified email with the subject and content",
            "parameters": {
                "type": "object",
                "properties": {
                    "Subject": {
                        "type": "string",
                        "description": "Subject of the email",
                    },
                    "Body": {
                        "type": "string",
                        "description": "The content of the email",
                    },
                    "Recipients": {
                        "type": "string",
                        "description": "The recipients' email addresses",
                    }
                },
                "required": ["Subject", "Body", "Recipients"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_shipments",
            "description": "查询某个客户的发运量",
            "parameters": {
                "type": "object",
                "properties": {
                    "customename": {
                        "type": "string",
                        "description": "name of the custome",
                    },
                },
                "required": ["customename"],
            },
        }
    },
]

st.sidebar.header("📃 Dialgue Session:")

def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

def send_email(recipient_email, subject, body):
    # 参数校验
    if recipient_email == '':
        return {"success": '0',"content": "邮件发送失败，你还没有告诉我收件人的邮箱地址"}
    if subject == '':
        return {"success": '0',"content": "邮件发送失败，你还没有告诉我邮件的主题"}
    return {"success": '1',"content": "邮件发送成功"}

def query_shipments(customename):
    if customename == "":
        return {"success": '0',"content": "你还没有告诉我客户的名称"}
    
    return {"success": '1',"content": "客户名：" + customename + ",当日发运量为：188.88吨"}

def main():
    st.title("🪪 AI Assistant")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": "你是人工智能助手，如果需要调用函数，不要填充测试内容"}]

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("What is your message?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        response = chat_completion_request(
            messages=st.session_state.messages,
            tools=tools
        )
        st.sidebar.json(st.session_state)
        st.sidebar.write(response)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):

            content = response.choices[0].message.content
            if response.choices[0].message.tool_calls == None:
                st.markdown(content)
                st.session_state.messages.append({"role": "assistant", "content": content})
            else:
                fn_name = response.choices[0].message.tool_calls[0].function.name
                fn_args = response.choices[0].message.tool_calls[0].function.arguments
                    
                if fn_name == "send_email":

                    def confirm_send_fn():
                        result = send_email(
                                    recipient_email=args["Recipients"],
                                    subject=args["Subject"],
                                    body=args["Body"],
                                )
                    
                        if (result["success"] == "1"):
                            st.markdown("邮件已发送")
                            st.session_state.messages.append({"role": "assistant", "content": "邮件已发送，还需要什么帮助吗？"})
                            # reflash sidebar
                            st.sidebar.json(st.session_state)
                            st.sidebar.write(response)
                        else:
                            st.markdown("邮件发送失败，" + result["content"])
                            st.session_state.messages.append({"role": "assistant", "content": "邮件发送失败，" + result["content"]})
                            # reflash sidebar
                            st.sidebar.json(st.session_state)
                            st.sidebar.write(response)

                    
                
                    def cancel_send_fn():    
                        st.markdown("邮件已取消，还需要什么帮助吗？")
                        st.session_state.messages.append({"role": "assistant", "content": "邮件已取消，还需要什么帮助吗？"})
                        # reflash sidebar
                        st.sidebar.json(st.session_state)
                        st.sidebar.write(response)


                    args = json.loads(fn_args)
                    # 参数判断
                    if args['Recipients'] == '' or args['Subject'] == '':
                        st.markdown("发邮件需要告诉我收件人的邮箱地址、主题和内容")
                        st.session_state.messages.append({"role": "assistant", "content": "发邮件需要告诉我收件人的邮箱地址、主题和内容"})
                        # reflash sidebar
                        st.sidebar.json(st.session_state)
                        st.sidebar.write(response)
                        return

                    st.markdown("邮件内容如下：")
                    st.markdown("发件人: cuifeng@163.com")
                    st.markdown(f"收件人: {args['Recipients']}")
                    st.markdown(f"主题: {args['Subject']}")
                    st.markdown(f"内容: {args['Body']}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.button(
                            label="✅确认发送邮件", 
                            on_click=confirm_send_fn)
                    with col2:
                        st.button(
                            label="❌取消发送邮件",
                            on_click=cancel_send_fn
                        )

                if fn_name == "query_shipments":

                    def confirm_query_fn():
                        result = query_shipments(args["customename"] )
                    
                        if (result["success"] == "1"):
                            st.markdown("客户发运量查询成功，" + result["content"])
                            st.session_state.messages.append({"role": "assistant", "content": "客户发运量查询成功，" + result["content"]})
                            # reflash sidebar
                            st.sidebar.json(st.session_state)
                            st.sidebar.write(response)
                        else:
                            st.markdown("客户发运量查询失败，" + result["content"])
                            st.session_state.messages.append({"role": "assistant", "content": "客户发运量查询失败，" + result["content"]})
                            # reflash sidebar
                            st.sidebar.json(st.session_state)
                            st.sidebar.write(response)

                    
                
                    def cancel_query_fn():    
                        st.markdown("邮件已取消，还需要什么帮助吗？")
                        st.session_state.messages.append({"role": "assistant", "content": "邮件已取消，还需要什么帮助吗？"})
                        # reflash sidebar
                        st.sidebar.json(st.session_state)
                        st.sidebar.write(response)

                    args = json.loads(fn_args)
                    # 参数判断
                    if args['customename'] == '':
                        st.markdown("请告诉我客户的名称")
                        st.session_state.messages.append({"role": "assistant", "content": "请告诉我客户的名称"})
                        # reflash sidebar
                        st.sidebar.json(st.session_state)
                        st.sidebar.write(response)
                        return
                    
                    st.markdown("查询客户发运量：")
                    st.markdown(f"要查询的客户: {args['customename']}")


                    col1, col2 = st.columns(2)
                    with col1:
                        st.button(
                            label="✅确认查询", 
                            on_click=confirm_query_fn)
                    with col2:
                        st.button(
                            label="❌取消查询",
                            on_click=cancel_query_fn
                        )


if __name__ == "__main__":
    main()
