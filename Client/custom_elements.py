from PyQt5.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, QFormLayout

class CreateUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.username=QLineEdit(self)
        self.username.setMaxLength(20)
        self.password=QLineEdit(self)
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMaxLength(50)
        self.confirm_password=QLineEdit(self)
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setMaxLength(50)

        self.buttonBox=QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)

        layout=QFormLayout(self)
        layout.addRow("username", self.username)
        layout.addRow("password", self.password)
        layout.addRow("confirm password", self.confirm_password)
        layout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def getResult(self):
        return self.username.text(), self.password.text(), self.confirm_password.text()
