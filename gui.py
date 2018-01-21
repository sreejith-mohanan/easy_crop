from tkinter import *
from PIL import Image, ImageTk
from tkinter.filedialog import askopenfilename, askdirectory
import os, glob


class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise (TclError, "cannot use pack with this widget")

    def place(self, **kw):
        raise (TclError, "cannot use place with this widget")


class Application():
    def __init__(self, main, win_width=900, win_height=540):

        self.os = os.name

        # list of image paths
        self.image_list = []
        # keeping an index for the current image in operation
        self.current_image_index = 0

        # keep the count of number of crops per image, used for uniquely naming the image
        self.crop_count=0

        # directory choosed
        self.data_path = StringVar()
        self.data_path.set("No directory set, Please set the directory to continue")

        # current crop size 32, 64, 128 or 256
        self.size_value = IntVar()
        self.size_value.set(32)

        # for mouse tracking
        self.is_rectangle_selected=False

        # save current rectangle start positions
        self.rect_x = 0
        self.rect_y = 0

        # image width and height
        self.image_width = 0
        self.image_height = 0

        self.frame = Frame(main)
        self.frame.grid(row=0, column=0, columnspan=8, sticky=N+W+S+E)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.scrollbar_x = AutoScrollbar(self.frame, orient=HORIZONTAL)
        self.scrollbar_y = AutoScrollbar(self.frame)

        self.canvas = Canvas(self.frame, xscrollcommand=self.scrollbar_x.set, yscrollcommand=self.scrollbar_y.set, width=win_width, height=win_height, relief=FLAT, bg='white')
        self.canvas.grid(row=0, column=0)

        self.scrollbar_x.config(command= self.canvas.xview)
        self.scrollbar_x.grid(row=1, column=0, sticky=E+W)

        # the below line is the default way, but i override this, see scroll_y_move()
        # self.scrollbar_y.config(command=self.canvas.yview)

        self.scrollbar_y.config(command=self.canvas.yview)
        self.scrollbar_y.grid(row=0, column=1, sticky=N+S)

        # binding key events to the main window 'a' or up arrow will increase the crop
        #  window size, 's' or down will decrease it
        main.bind('<a>', self.on_up_arrow)
        main.bind('<s>', self.on_down_arrow)
        main.bind('<Up>', self.on_up_arrow)
        main.bind('<Down>', self.on_down_arrow)
        main.bind('<Return>', self.on_enter_key)
        main.bind('<space>', self.on_space_key)

        # main.bind('<Configure>', self.on_resize_window)

        # binding mouse event to drag the crop window
        self.canvas.bind('<Motion>', self.on_mouse_move)
        self.canvas.bind('<Button-1>', self.rect_select)
        self.canvas.bind('<ButtonRelease-1>', self.rect_deselect)
        self.canvas.bind('<Button-4>', self.on_mouse_wheel)
        self.canvas.bind('<Button-5>', self.on_mouse_wheel)

        self.scroll_x = 0
        self.scroll_y = 0


        # put a default image for some indication
        #---->
        self.img = Image.open('bg.png')
        self.photo_img = ImageTk.PhotoImage(self.img)

        # self.img = None
        # self.photo_img = None

        #---->

        self.image_on_canvas = self.canvas.create_image(win_width/2, win_height/2, anchor=CENTER, image=self.photo_img)

        self.rectangle = self.canvas.create_rectangle(self.rect_x, self.rect_y, 32, 32, outline='white')

        # first row
        self.directory_label = Label(main, textvariable= self.data_path, relief=FLAT)
        self.directory_label.grid(row=1, column=0, columnspan=8)
        self.button_load_dir = Button(main, text='Folder Load', command=self.load_data_dir)
        self.button_load_dir.grid(row=2, column=0, columnspan=8)

        # second row
        self.size_8_radio = Radiobutton(main, text="8x8      ", variable=self.size_value, value=8, command=self.size_change)
        self.size_8_radio.grid(row=3, column=0, sticky=E+W)
        self.size_16_radio = Radiobutton(main, text="16x16   ", variable=self.size_value, value=16, command=self.size_change)
        self.size_16_radio.grid(row=3, column=1, sticky=E+W)
        self.size_32_radio = Radiobutton(main, text="32x32   ", variable=self.size_value, value=32, command=self.size_change)
        self.size_32_radio.grid(row=3, column=2, sticky=E+W)
        self.size_64_radio = Radiobutton(main, text="64x64   ", variable=self.size_value, value=64, command=self.size_change)
        self.size_64_radio.grid(row=3, column=3, sticky=E+W)
        self.size_128_radio = Radiobutton(main, text="128x128", variable=self.size_value, value=128, command=self.size_change)
        self.size_128_radio.grid(row=3, column=4, sticky=E+W)
        self.size_256_radio = Radiobutton(main, text="256x256", variable=self.size_value, value=256, command=self.size_change)
        self.size_256_radio.grid(row=3, column=5, sticky=E+W)
        self.size_512_radio = Radiobutton(main, text="512x512", variable=self.size_value, value=512, command=self.size_change)
        self.size_512_radio.grid(row=3, column=6, sticky=E+W)
        self.button_save = Button(main, text='Save', command=self.save_croped_image, fg='red')
        self.button_save.grid(row=3, column=7, sticky=E+W)

        # third row
        self.button_previous = Button(main, text='Previous', command=self.show_previous)
        self.button_previous.grid(row=4, column=0, columnspan=4, sticky=E+W)
        self.button_next = Button(main, text='Next', command=self.show_next)
        self.button_next.grid(row=4, column=4, columnspan=4, sticky=E+W)

        #fourth row
        self.button_load_img = Button(main, text='File Open', command=self.load_img_random)
        self.button_load_img.grid(row=5, columnspan=8, sticky=E+W)

    def load_img(self, filename):
        """
        Load the given image into the application
        :param filename:
        :return:
        """
        self.img = Image.open(filename)
        self.image_width = self.img.width
        self.image_height = self.img.height
        self.photo_img = ImageTk.PhotoImage(self.img)
        self.canvas.itemconfig(self.image_on_canvas, anchor=NW, image=self.photo_img)
        self.canvas.coords(self.image_on_canvas, 0,0)

        self.canvas.config(scrollregion=(0, 0, self.image_width, self.image_height))
        print(self.current_image_index, '|', filename)

    def load_img_random(self):
        """
        handler function for the load image button
        :return:
        """
        name = askopenfilename()
        self.load_img(name)
        self.crop_count = 0

    def load_data_dir(self):
        """
        handler function for the load directory button
        :return:
        """
        dir_name = askdirectory()
        self.image_list = glob.glob(dir_name + '/data/*')
        # print(self.image_list)
        self.data_path.set(dir_name)
        self.create_directories()
        self.load_img(self.image_list[self.current_image_index])

    def save_croped_image(self):
        """
        Saves the cropped image
        :return:
        """
        root_dir = str(self.data_path.get())
        x1, y1, x2, y2 = self.canvas.coords(self.rectangle)
        if self.os == 'nt':
            filename = (self.image_list[self.current_image_index].split('\\')[-1]).split('.')[0]
        else:
            filename = (self.image_list[self.current_image_index].split('/')[-1]).split('.')[0]

        try:
            img2 = self.img.crop((x1, y1, x2, y2))
        except Exception as e:
            print(e.args)
            return
        window_size = int(self.size_value.get())
        if window_size == 512:
            img2.save(root_dir + "/512x512/" + filename + '_' + str(self.crop_count) + ".png")
            print('saving to: ', root_dir + "/512x512/" + filename + '_' + str(self.crop_count) + ".png")
        if window_size == 256:
            img2.save(root_dir + "/256x256/" + filename + '_' + str(self.crop_count) + ".png")
            print('saving to: ', root_dir + "/256x256/" + filename + '_' + str(self.crop_count) + ".png")
        if window_size == 128:
            img2.save(root_dir + "/128x128/" + filename + '_' + str(self.crop_count) + ".png")
            print('saving to: ', root_dir + "/128x128/" + filename + '_' + str(self.crop_count) + ".png")
        if window_size == 64:
            img2.save(root_dir + "/64x64/" + filename + '_' + str(self.crop_count) + ".png")
            print('saving to: ', root_dir + "/64x64/" + filename + '_' + str(self.crop_count) + ".png")
        if window_size == 32:
            img2.save(root_dir + "/32x32/" + filename + '_' + str(self.crop_count) + ".png")
            print('saving to: ', root_dir + "/32x32/" + filename + '_' + str(self.crop_count) + ".png")
        if window_size == 16:
            img2.save(root_dir + "/16x16/" + filename + '_' + str(self.crop_count) + ".png")
            print('saving to: ', root_dir + "/16x16/" + filename + '_' + str(self.crop_count) + ".png")
        if window_size == 8:
            img2.save(root_dir + "/8x8/" + filename + '_' + str(self.crop_count) + ".png")
            print('saving to: ', root_dir + "/8x8/" + filename + '_' + str(self.crop_count) + ".png")

        self.crop_count += 1

    def show_previous(self):
        """
        Show the previous image
        :return:
        """
        if self.current_image_index ==0:
            return
        self.current_image_index -= 1
        self.load_img(self.image_list[self.current_image_index])
        self.crop_count = 0

    def show_next(self):
        """
        Shows the next image
        :return:
        """
        if self.current_image_index == (len(self.image_list) -1):
            return
        self.current_image_index +=1
        self.load_img(self.image_list[self.current_image_index])
        self.crop_count = 0

    def create_directories(self):
        """
        Helper function to create required directories
        :return:
        """
        root_dir = str(self.data_path.get())
        # create directories if not exist
        print('creating directories /8x8/ /16x16/ /32x32/ /64x64/ /128x128/ /256x256/')

        if not os.path.exists(root_dir + '/8x8/'):
            os.makedirs(root_dir + '/8x8/')
        if not os.path.exists(root_dir + '/16x16/'):
            os.makedirs(root_dir + '/16x16/')
        if not os.path.exists(root_dir + '/32x32/'):
            os.makedirs(root_dir + '/32x32/')
        if not os.path.exists(root_dir + '/64x64/'):
            os.makedirs(root_dir + '/64x64/')
        if not os.path.exists(root_dir + '/128x128/'):
            os.makedirs(root_dir + '/128x128/')
        if not os.path.exists(root_dir + '/256x256/'):
            os.makedirs(root_dir + '/256x256/')
        if not os.path.exists(root_dir + '/512x512/'):
            os.makedirs(root_dir + '/512x512/')

    def size_change(self):
        """
        Handler function to crop window size change
        :return:
        """
        self.canvas.coords(self.rectangle, self.rect_x, self.rect_y, self.rect_x + int(self.size_value.get()),
                           self.rect_y + int(self.size_value.get()))

    def on_mouse_wheel(self, event):
        if event.num == 4:
            self.canvas.xview('scroll', -1, 'units')
        elif event.num == 5:
            self.canvas.xview('scroll', 1, 'units')

    def rect_select(self, event):
        """
        Key pressed
        :param event:
        :return:
        """
        self.is_rectangle_selected = True

    def rect_deselect(self, event):
        """
        Key released
        :param event:
        :return:
        """
        self.is_rectangle_selected = False

    def on_enter_key(self, event):
        """
        event handler for enter key press
        :param event:
        :return:
        """
        self.save_croped_image()

    def on_space_key(self, event):
        """
        Event handler function for space bar ( next image)
        :param event:
        :return:
        """
        self.show_next()

    def on_mouse_move(self, event):
        """
        Event handler for dragging the window
        :param event:
        :return:
        """
        if self.is_rectangle_selected:
            self.scroll_x = int(self.scrollbar_x.get()[0] * self.image_width)
            self.scroll_y = int(self.scrollbar_y.get()[0] * self.image_height)
            self.rect_x = event.x + self.scroll_x
            self.rect_y = event.y + self.scroll_y
            self.canvas.coords(self.rectangle, self.rect_x, self.rect_y, self.rect_x + int(self.size_value.get()), self.rect_y + int(self.size_value.get()))

    def on_up_arrow(self, event):
        """
        Event handler for up arrow pressing
        :param event:
        :return:
        """
        print('increasing')
        window_size = int(self.size_value.get())
        if window_size == 8:
            self.size_value.set(16)
        if window_size == 16:
            self.size_value.set(32)
        if window_size == 32:
            self.size_value.set(64)
        if window_size == 64:
            self.size_value.set(128)
        if window_size == 128:
            self.size_value.set(256)
        if window_size == 256:
            self.size_value.set(512)
        self.size_change()

    def on_down_arrow(self, event):
        """
        Event handler for down arrow pressing
        :param event:
        :return:
        """
        print('decreasing')
        window_size = int(self.size_value.get())
        if window_size == 512:
            self.size_value.set(256)
        if window_size == 256:
            self.size_value.set(128)
        if window_size == 128:
            self.size_value.set(64)
        if window_size == 64:
            self.size_value.set(32)
        if window_size == 32:
            self.size_value.set(16)
        if window_size == 16:
            self.size_value.set(8)
        self.size_change()


master = Tk()
# master.resizable(width=False, height=False)
Application(master, 1000, 540)
mainloop()
