from PyQt5.QtWidgets import *
def main(): 
    app =QApplication([]) # create a window
    window = QWidget()
    
    runButton = QPushButton(window) # run button
    runButton.setText("Run")
    runButton.move(50, 50)

    exitButton = QPushButton(window) # exit button
    exitButton.setText("Exit")
    exitButton.move(50, 100)

    window.setGeometry(100, 100, 320, 200)
    window.setWindowTitle("Golf balance window")
    window.show() # show window
    app.exec_()


if __name__ == '__main__':
    main()
