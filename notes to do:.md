notes to do:

a) work with footer container later
b) add get_css function in utils or config files. 
c) add utils/config files,  make sure initial_prompt is there
d)change AI: and Human:  in if loops and memory
e) add get_chat_message fucntion
f) you are using the session state memory for model parameters, work on it later, might not be needed
G)#try remove replybox container first markdown (empty)
h)Add files for the writing animation or remove the snippet. It adds 3 dots animation, also in th ewriting_animation.empty()
i)add function chat_bot presponse
j)what to return in main?
k) do the initalizing page config
ADD AWS FUNC FILE TRO SAVE, AND KEYS TO REPO


[DONE]] YOU NEED TO WORK ON GET_CHAT_MESSAGE FUNCTION AND UPLOADING THE ARTIFACT (IMAGES) IN THE LOCAL

[DONE]  check if the followup prompt is workiung , depends on your get_chat_message


2. St.page_layout as wide is not working somehow, see if there is issue of css, 
3. Fix CSS colour issues
4. then save threadIds (minimum) and conversations in dynamoDB. check on AWS console
5. Thn deploy on an EC2 for app to run
6. then use auth to login in app on internet


to do in app
1. add a sidebar or new button for "New journal"
2. then use syt.chear_cache and st.rerunn to rerun stuff. would work
3. put a button only, see if you can soplit streamlit in 2 colsm just for the button

if st.button("Refresh and Clear Cache"):
    st.cache_data.clear()
    st.rerun()

new sesison not working, handle later
---