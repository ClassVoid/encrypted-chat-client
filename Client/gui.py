import re
import socket
import sys
import netifaces as ni

from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QThread, QEvent, Qt
from PyQt5.QtGui import QColor

from workers import *
from custom_elements import *


class UI(QtWidgets.QMainWindow, QObject):
    def __init__(self, parent=None):
        # super(UI, self).__init__(parent)
        QtWidgets.QMainWindow.__init__(self)
        QObject.__init__(self)
        uic.loadUi("chat_gui.ui", self)
        self.__extract_components()
        self.__configure_signals()

        '''
        ("darkgreen",Qt.darkGreen), ("darkred",Qt.darkRed),
                        ("darkmagenta",Qt.darkMagenta), ("magenta",Qt.magenta)
                        ("red", Qt.red),
        '''

        self.color_map = [("gold", QColor(255, 215, 0)), ("orangered", QColor(255, 69, 0)),
                          ("firebrick", QColor(178, 34, 34)), ("lawngreen", QColor(124, 252, 0))
                          ]
        # asocierea dintre user din chat si o culoare din paleta de culori
        self.user_color = {}
        self.can_get_msg = True
        self.stream_on = False
        self.chat_selected=False

        self.show()

    def __extract_components(self):
        self.central_widget = self.findChild(QtWidgets.QWidget, "centralwidget")

        self.stacked_widget = self.central_widget.findChild(QtWidgets.QStackedWidget, "stackedWidget")
        self.stacked_widget.setCurrentIndex(0)
        # Login Page

        self.page_1 = self.stacked_widget.widget(0)
        self.login_btn = self.page_1.findChild(QtWidgets.QPushButton, "pushButton")
        self.create_user_btn = self.page_1.findChild(QtWidgets.QPushButton, "pushButton_3")
        self.username_txt = self.page_1.findChild(QtWidgets.QLineEdit, "lineEdit")
        self.password_txt = self.page_1.findChild(QtWidgets.QLineEdit, "lineEdit_2")
        self.password_txt.setEchoMode(QtWidgets.QLineEdit.Password)

        # Main Page
        self.page_2 = self.stacked_widget.widget(1)
        self.current_chat = self.page_2.findChild(QtWidgets.QLabel, "label_3")
        self.current_user = self.page_2.findChild(QtWidgets.QLabel, "label_4")
        self.new_chat_btn = self.page_2.findChild(QtWidgets.QPushButton, "pushButton_5")
        self.send_btn = self.page_2.findChild(QtWidgets.QPushButton, "pushButton_6")
        self.add_user_btn = self.page_2.findChild(QtWidgets.QPushButton, "pushButton_7")
        self.logout_btn = self.page_2.findChild(QtWidgets.QPushButton, "pushButton_8")
        self.delete_chat_btn = self.page_2.findChild(QtWidgets.QPushButton, "pushButton_9")
        self.chat_list = self.page_2.findChild(QtWidgets.QListWidget, "listWidget")
        self.chat_browser = self.page_2.findChild(QtWidgets.QTextBrowser, "textBrowser")
        self.message_box = self.page_2.findChild(QtWidgets.QTextEdit, "textEdit")
        self.stream_btn = self.page_2.findChild(QtWidgets.QPushButton, "pushButton_2")
        self.watch_stream_btn = self.page_2.findChild(QtWidgets.QPushButton, "pushButton_4")
        self.chat_users_list = self.page_2.findChild(QtWidgets.QListWidget, "listWidget_2")
        self.delete_account_btn = self.page_2.findChild(QtWidgets.QPushButton, "pushButton_11")

        # self.preferences_act = QtWidgets.QAction("Preferences", self)
        # self.findChild(QtWidgets.QMenuBar, "menubar") \
        #    .findChild(QtWidgets.QMenu, "menuSettings") \
        #    .addAction(self.preferences_act)
        # print(f"Preferances= {self.preferences_act}")
        # self.chat_list.addItem("chat_1")
        # self.chat_list.addItem("chat_2")
        # self.chat_list.clear()

    def __configure_signals(self):
        # Login page
        self.login_btn.clicked.connect(self.__login_pressed)
        self.create_user_btn.clicked.connect(self.__create_user_pressed)

        # Main Page
        self.new_chat_btn.clicked.connect(self.__new_chat_pressed)
        self.send_btn.clicked.connect(self.__send_pressed)
        self.add_user_btn.clicked.connect(self.__add_user_pressed)
        self.logout_btn.clicked.connect(self.__logout_pressed)
        self.delete_chat_btn.clicked.connect(self.__delete_chat_pressed)
        self.chat_list.itemClicked.connect(self.__select_chat_pressed)
        self.stream_btn.clicked.connect(self.__stream_pressed)
        self.watch_stream_btn.clicked.connect(self.__watch_stream_pressed)
        self.chat_users_list.itemClicked.connect(self.__select_user_pressed)
        self.delete_account_btn.clicked.connect(self.__delete_account_pressed)
        self.message_box.installEventFilter(self)

        # text input size config
        self.username_txt.setMaxLength(20)
        # self.password_txt.setMaxLength(50)

    def __login_pressed(self):
        username = self.username_txt.text()
        password = self.password_txt.text()

        print(f"Login\nUsername: {username}\nPassword: {password}")
        '''
            Send the credentials to the server
            If everything works fine then save the data from the server
        '''
        self.login_btn.setEnabled(False)
        self.login_thread = QThread()
        self.login_worker = LoginWorker(username, password)
        self.login_worker.moveToThread(self.login_thread)

        self.login_thread.started.connect(self.login_worker.run)
        self.login_worker.finished.connect(self.login_thread.quit)
        self.login_worker.finished.connect(self.__login_callback)

        self.login_worker.finished.connect(self.login_worker.deleteLater)
        self.login_thread.finished.connect(self.login_thread.deleteLater)

        self.login_thread.start()

        self.login_thread.finished.connect(lambda: self.login_btn.setEnabled(True))

    def __login_callback(self, res: requests.Response, password: str):
        '''
        You must check the status to make sure everything went fine
        :param res:
        :param password:
        :return:
        '''
        print(res.status_code)
        # TO_DO add a try catch block, in case the password does not match
        if res.status_code == 404:
            QtWidgets.QMessageBox.critical(self, "Login Error", "Incorrect username")
        elif res.status_code == 503:
            QtWidgets.QMessageBox.critical(self, "Server Error", "Seems that the server is unavailable")
        else:
            try:
                privateKey = decryptAES(f"{res.json()['encryptedPriKey']}", password)

                self.credentials: Dict[str, str] = {"username": f"{res.json()['username']}",
                                                    "pubKey": f"{res.json()['pubKey']}",
                                                    "PriKey": f"{privateKey}"}

                print(self.credentials)
                if res.status_code == 200:
                    self.current_user.setText(self.credentials['username'])
                    self.send_btn.setEnabled(False)
                    self.add_user_btn.setEnabled(False)
                    self.delete_chat_btn.setEnabled(False)
                    self.stream_btn.setEnabled(False)
                    self.watch_stream_btn.setEnabled(True)
                    self.menuBar().setEnabled(True)
                    self._refresh_chats()
                    self._switch(1)
            except UnicodeDecodeError:
                QtWidgets.QMessageBox.critical(self, "Login Error", "Incorrect password")

    def __create_user_pressed(self):
        # username = self.username_txt.text()
        # password = self.password_txt.text()
        create_dialog = CreateUserDialog(self)
        if create_dialog.exec():
            username, password, confirm_password = create_dialog.getResult()
            if password != confirm_password:
                QtWidgets.QMessageBox.critical(self, "INPUT ERROR", "Passwords don't match")
                return

            if len(password) < 4:
                QtWidgets.QMessageBox.critical(self, "INPUT ERROR", "Password must exceed 4 characters")
                return

            print(f"Create Account\nUsername: {username}\nPassword: {password}")
            '''
                Create the credentials and send them to the server
                Check for errors
            '''
            self.create_user_btn.setEnabled(False)
            self.login_btn.setEnabled(False)
            self.signup_thread = QThread()
            self.signup_worker = SignUpWorker(username, password)

            self.signup_worker.moveToThread(self.signup_thread)
            self.signup_thread.started.connect(self.signup_worker.run)
            self.signup_worker.finished.connect(self.signup_thread.quit)
            self.signup_worker.finished.connect(self.__signup_callback)
            self.signup_worker.finished.connect(self.signup_worker.deleteLater)
            self.signup_thread.finished.connect(self.signup_thread.deleteLater)
            self.signup_thread.start()
            self.signup_thread.finished.connect(lambda: self.create_user_btn.setEnabled(True))
            self.signup_thread.finished.connect(lambda: self.login_btn.setEnabled(True))

    def __signup_callback(self, res: requests.Response.__class__):
        '''
        You have to check if the response is good
        :param res:
        :return:
        '''
        print(res)
        if res.status_code == 409:
            QtWidgets.QMessageBox.critical(self, "Sign up Error", "Username is already taken")

        if res.status_code == 503:
            QtWidgets.QMessageBox.critical(self, "Server Error", "Seems that the server is unavailable")

    def __new_chat_pressed(self):
        chat_name, ok = QtWidgets.QInputDialog().getText(self, "Create chat", "Enter chat name")

        if ok and len(chat_name) <= 20:
            print(f"chat name is {chat_name}")
            self.new_chat_btn.setEnabled(False)
            self.new_chat_thread = QThread()
            self.new_chat_worker = NewChatWorker(self.credentials, chat_name)
            self.new_chat_worker.moveToThread(self.new_chat_thread)

            self.new_chat_thread.started.connect(self.new_chat_worker.run)
            self.new_chat_worker.finished.connect(self.new_chat_thread.quit)
            self.new_chat_worker.finished.connect(self.__new_chat_callback)

            self.new_chat_worker.finished.connect(self.new_chat_worker.deleteLater)
            self.new_chat_thread.finished.connect(self.new_chat_thread.deleteLater)

            self.new_chat_thread.start()
            self.new_chat_thread.finished.connect(lambda: self.new_chat_btn.setEnabled(True))
        elif ok:
            QtWidgets.QMessageBox.critical(self, "ERROR", "Chat name is too long\nMaximum length is 20 characters")

    def __new_chat_callback(self, res: requests.Response, chat_name: str):
        if res.status_code == 201:
            # make it async
            add_user_res = addUser(self.credentials, self.credentials['username'], chat_name)
            if add_user_res.status_code == 201:
                # make it async
                self._refresh_chats()
        elif res.status_code == 409:
            QtWidgets.QMessageBox.critical(self, "ERROR, CREATE CHAT", res.text)

    def _refresh_chats(self):
        chats_res = getUserChats(self.credentials)
        chats = chats_res.json()
        # print(chats)
        self.chat_list.clear()
        for chat in chats:
            self.chat_list.addItem(chat)

    def __send_pressed(self):
        print("send")
        '''
            encrypt the message
            send the message
            updateChat()
        '''
        if not self.chat_selected:
            return

        message = self.message_box.toPlainText()
        if len(message) < 500:
            sendMessage(self.credentials['username'], self.current_chat.text(), self.chat_key, message)
            self.message_box.setText("")
            self._update_chat()
        else:
            QtWidgets.QMessageBox.critical(self, "ERROR", f"Message size must be under 500 characters\n"
                                                          f"Current Message size is {len(message)} characters")

    def __add_user_pressed(self):
        print("add user")
        username, ok = QtWidgets.QInputDialog().getText(self, "Add user", "Enter user name")

        if ok and len(username) < 20:
            try:
                addUser(self.credentials, username, self.current_chat.text())
                self._update_user_list()
            except:
                QtWidgets.QMessageBox.critical(self, "Error", f"User {username} not found")
        elif ok:
            QtWidgets.QMessageBox.critical(self, "ERROR", f"Usernames are at max 20 characters\n"
                                                          f"This username has {len(username)} characters")

    def __logout_pressed(self):
        # you could clear the text boxes
        self.current_chat.setText("No Chat Selected")
        self.chat_selected=False
        self.message_box.setText("")
        self.chat_browser.setText("")
        self._close_stream()
        self.chat_users_list.clear()
        self.chat_list.clear()
        self.menuBar().setEnabled(False)
        self._switch(0)

    def __delete_chat_pressed(self):
        print("delete chat")
        '''
            call delete chat
            remove the chat from the list
        '''
        deleteChat(self.credentials, self.current_chat.text())
        self.chat_browser.setText("")
        self.current_chat.setText("No Chat Selected")
        self.chat_users_list.clear()
        self.chat_selected=False
        self.send_btn.setEnabled(False)
        self.delete_chat_btn.setEnabled(False)
        self.add_user_btn.setEnabled(False)
        self._refresh_chats()

    def __delete_account_pressed(self):
        reply = QtWidgets.QMessageBox.question(self, "Delete Account", "Are you sure you want to delete your account?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            print("Your account will be deleted")

            # send the delete request to the server
            deleteAccount(self.credentials)

            self.__logout_pressed()

    def __select_chat_pressed(self, item):
        # save the current chat
        self.current_chat.setText(item.text())
        '''
            get chat key
            decrypt chat key and save it
            call updateChat()
        '''
        self.send_btn.setEnabled(True)
        self.add_user_btn.setEnabled(True)
        self.stream_btn.setEnabled(True)
        self.chat_selected=True

        owner_name = getChatOwner(item.text()).text
        if owner_name == self.credentials['username']:
            self.delete_chat_btn.setEnabled(True)
        else:
            self.delete_chat_btn.setEnabled(False)

        self.chat_list.setEnabled(False)

        # get the chat key
        resp = getChatKey(self.credentials['username'], item.text())
        if resp.status_code != 200:
            QtWidgets.QMessageBox.critical(self, "ERROR", resp.text)
            self.chat_browser.setText("")
            self.current_chat.setText("No Chat Selected")
            self.chat_selected=False
            self.chat_users_list.clear()
            self.send_btn.setEnabled(False)
            self.delete_chat_btn.setEnabled(False)
            self.add_user_btn.setEnabled(False)
            self._refresh_chats()
            return

        encrypted_key = resp.text
        self.chat_key = decryptRSA(encrypted_key, self.credentials['PriKey'])

        self._update_user_list()
        self._update_chat()
        self.chat_list.setEnabled(True)

    def __select_user_pressed(self, item):
        print(f"user {item.text()} selected")

    def __stream_pressed(self):

        # self.stream_on = not self.stream_on

        # check to see if the stream is off
        if not self.stream_on:
            x = ni.gateways()
            y = x['default'][2][1]
            ip_address = ni.ifaddresses(y)[ni.AF_INET][0]['addr']
            default_server_address = f"rtmp://{ip_address}:1935/show/{self.credentials['username']}"
            input_server_address, ok = QtWidgets. \
                QInputDialog.getText(self,
                                     "Start streaming",
                                     "Insert the RTMP stream server IPv4 address\nBy default is the local address")
            server_address = ""
            # if the user wants to stream
            if ok:
                print("Stream Started")
                self.stream_on = True  # not self.stream_on
                if len(input_server_address) == 0 \
                        or re.search("^rtmp://\d+\.\d+\.\d+\.\d+:\d+/\w+/\w+$", input_server_address) is None:
                    server_address = default_server_address
                else:
                    server_address = input_server_address
                print(f"streaming to\t{server_address}")
                # send the address to the current chat
                sendMessage(self.credentials['username'], self.current_chat.text(),
                            self.chat_key, f"{self.credentials['username']} is streaming on {server_address}")
                self._update_chat()

                QtWidgets.QMessageBox.about(self, "Stream Info", f"The stream will start on address\n{server_address}")

                # self.watch_stream_btn.setEnabled(False)
                self.stream_btn.setText("Stop Stream")
                self.stream_thread = QThread()
                self.stream_worker = StreamSenderWorker(server_address)
                self.stream_worker.moveToThread(self.stream_thread)

                self.stream_worker.error_signal.connect(self.__on_stream_error)
                self.stream_thread.started.connect(self.stream_worker.run)
                self.stream_worker.finished.connect(self.stream_thread.quit)
                self.stream_worker.finished.connect(self.stream_worker.deleteLater)
                self.stream_thread.finished.connect(self.stream_thread.deleteLater)

                self.stream_thread.start()
        else:
            print("Stream Stopped")
            self.stream_btn.setText("Start Stream")
            self.stream_worker.stop()
            self.stream_on = False
            # self.watch_stream_btn.setEnabled(True)

    def __on_stream_error(self, err_msg):
        self.stream_worker.stop()
        self.stream_on = False
        self.stream_btn.setText("Start Stream")
        QtWidgets.QMessageBox.critical(self, "ERROR", err_msg)

    def __watch_stream_pressed(self):
        print("Watch stream")
        # text dialog box popup
        # !!! CHECK IF THE INPUT IS AN ADDRESS
        stream_address, ok = QtWidgets.QInputDialog.getText(self, "Connect to Stream",
                                                            "Insert the RTMP stream server IPv4 address")

        if ok and re.search("^rtmp://\d+\.\d+\.\d+\.\d+:\d+/\w+/\w+$", stream_address) is not None:
            self.watch_stream_btn.setEnabled(False)
            self.watch_stream_thread = QThread()
            self.watch_stream_worker = StreamConsumerWorker(stream_address)
            self.watch_stream_worker.moveToThread(self.watch_stream_thread)

            self.watch_stream_thread.started.connect(self.watch_stream_worker.run)
            self.watch_stream_worker.finished.connect(self.watch_stream_thread.quit)
            self.watch_stream_worker.finished.connect(self.watch_stream_worker.deleteLater)
            self.watch_stream_thread.finished.connect(self.watch_stream_thread.deleteLater)
            self.watch_stream_thread.finished.connect(lambda: self.watch_stream_btn.setEnabled(True))

            self.watch_stream_thread.start()

    def _update_chat(self):
        '''
        def updateChat():
                get the messages sent since yesterday
                decrypt the messages
                display the messages
        :return:
        '''
        if not self.chat_selected:
            return

        chat_name = self.current_chat.text()
        print(f"updating chat {chat_name}")

        # !!! make async
        # get messages
        x = datetime.datetime.now() - datetime.timedelta(days=1)
        date_time = x.strftime("%Y-%m-%dT%H:%M:%S")
        messages = getMessages(chat_name, date_time).json()
        print(messages)

        # chat_text = ""
        msg_elem = ""
        # decrypt messages
        for i in range(len(messages)):
            msg_date = datetime.datetime.fromisoformat(messages[i]['date'])
            chat_text = f"{messages[i]['author']}" \
                        f"[{msg_date.hour}:{msg_date.minute} {msg_date.day}/{msg_date.month}/{msg_date.year}]:" \
                        f" {decryptAES(messages[i]['encryptedMsg'], self.chat_key)}"

            if messages[i]['author'] == self.credentials['username']:
                msg_elem += f"<div style=\"color:darkorange\">{chat_text}</div>"
            else:
                msg_elem += f"<div style=\"color:{self.user_color[messages[i]['author']][0]}\">{chat_text}</div>"
        print(msg_elem)
        self.chat_browser.setText(msg_elem)

    def _update_user_list(self):

        # ideal ar fi sa utilizez workeri
        chat_name = self.current_chat.text()
        self.user_color.clear()
        try:
            user_list = updateUserList(self.credentials, chat_name).json()
            self.chat_users_list.clear()
            for username in user_list:
                item = QtWidgets.QListWidgetItem(username)
                # verific daca eu sunt userul, daca da colorez cu albastru
                if username == self.credentials['username']:
                    item.setForeground(QColor(255, 140, 0))
                else:
                    color = self.color_map[
                        user_list.index(username) % len(self.color_map)]  # random.choice(self.color_map)
                    self.user_color[username] = color
                    item.setForeground(color[1])
                self.chat_users_list.addItem(item)
        except:
            QtWidgets.QMessageBox.critical(self, "Error", "Something went wrong when acquiring the user list")

    def _switch(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def _close_stream(self):
        if hasattr(self, 'stream_worker') and self.stream_on:
            self.stream_worker.stop()
            self.stream_btn.setText("Start Stream")
            self.stream_on = False

        if hasattr(self, 'watch_stream_worker'):
            self.watch_stream_worker.stop()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self._close_stream()
            event.accept()
        else:
            event.ignore()

    def eventFilter(self, obj, event) -> bool:
        if obj is self.message_box \
                and event.type() == QEvent.Type.KeyPress \
                and event.key() == Qt.Key_Return:
            self.__send_pressed()
            return True

        return super(UI, self).eventFilter(obj, event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = UI()
    app.setStyleSheet(open("styles/dark_orange_theme.qss").read())
    window.show()
    sys.exit(app.exec_())


main()
