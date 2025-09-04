#!/usr/bin/python
from __future__ import print_function
import cv2, numpy as np
from sklearn.cluster import KMeans
from skimage import io
from os import listdir, makedirs, system, remove, rmdir
from os.path import isfile, join, exists, basename
import sys, getopt
import threading, Queue
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import time
import csv

# file management
directory_name = 'tmp'
in_file = ''
out_file = 'out.png'

# output resolutions
resolutions = {}
resolution = (300, 50)

# num threads
threads = 1

# list of colors (RGB, ID)
colors = []

# counts # of processed images per thread
counts = [0]

# number of frames per second to capture from the video
rate = ''

# files to be processed
file_queue = Queue.Queue()

# pid of file generation
gen_id = 0

# whether to delete files
clean = False

# whether to display the result
show = False

# title to print
title = ""

# set the available resolutions
def setup_resolutions():
	global resolutions
	global resolution
	resolutions['8000'] = (7680, 4320)
	resolutions['4000'] = (3840, 2160)
	resolutions['1080'] = (1920, 1080)
	resolutions['720'] = (1280, 720)
	resolutions['480'] = (852, 480)
	resolutions['360'] = (640, 360)
	resolutions['240'] = (320, 240)
	resolution = resolutions['1080']

# main function
def main(argv):
	global directory_name
	global in_file
	global out_file
	global resolutions
	global resolution
	global threads
	global counts
	global rate
	global file_queue
	global gen_id
	global clean
	global show
	global title
	setup_resolutions()

	# define command-line parameters
	try:
		opts, args = getopt.getopt(argv, "cd:hi:l:n:o:q:r:s:t:w:")
	except getopt.GetoptError:
		print('Error: check arguments - ', argv)
		print_help()
		exit(2)

	l = 0
	w = 0
	for opt, arg in opts:
		if opt == '-h':
			print_help()
			exit()
		elif opt == '-d':
			directory_name = arg
		elif opt == '-i':
			in_file = arg
		elif opt == '-q':
			if arg not in resolutions.keys():
				print('Error: invalid resolution - ' + arg)
				print_help()
				exit(2)
			resolution = resolutions[arg]
		elif opt == '-o':
			out_file = arg
		elif opt == '-t':
			threads = int(arg)
			counts = [0] * threads
		elif opt == '-r':
			rate = arg
		elif opt == '-c':
			clean = True
		elif opt == '-s':
			show = True
		elif opt == '-l':
			l = float(arg)
		elif opt == '-w':
			w = float(arg)
		elif opt == '-n':
			title = str(arg)

	if not l == 0:
		resolution = (int(l * 300), resolution[1])
	if not w == 0:
		resolution = (resolution[0], int(w * 300))

	if in_file.endswith('csv'):
		generate_from_csv()

	start = time.time()

	# create image directory if it doesn't exist
	if not exists(directory_name):
		makedirs(directory_name)

	watcher = Observer()
	# if in_file exists, create images from video
	if not in_file == '':
		# set up file watcher
		event_handler = PatternMatchingEventHandler("*.jpeg", "", True, True)
		event_handler.on_created = on_created
		watcher.schedule(event_handler, directory_name, recursive=False)
		watcher.start()

		print("Generating images from " + in_file + " in " + directory_name + "...")
		gen_id = threading.Thread(target=generate_images)
		gen_id.start()
	else:
		# get list of files
		files = [join(directory_name, f) for f in listdir(directory_name) if isfile(join(directory_name, f))]
		# put in order
		files = sorted(files)
		for f in files:
			file_queue.put(f)
	# keep track of threads
	ids = []
	# generate threads
	for index in range(threads):
		x = threading.Thread(target=process_images, args=(index,))
		ids.append(x)
		x.start()

	# Report thread progress
	if not in_file == '':
		gen_id.join()
		gen_id = 0

	while not file_queue.empty():
		sc = sum(counts)
		sz = file_queue.qsize()
		total = sc + sz
		percent = round(((0.0 + sc) / total) * 100, 2)
		now = time.time()
		print("\rProcessing Images with " + str(threads) + " threads: " + \
			str(sc) + ' images processed, ' + str(sz) + " images remaining, " + \
			str(percent) + "%. time=" + get_time(now-start), end='')
		time.sleep(5)

	# Join threads back together
	for x in ids:
		x.join()
	end = time.time()
	print("\nDone! Processed " + str(sum(counts)) + " images in " + get_time(end-start) + ". Outputing to " + out_file + "...")

	if not in_file == '':
		watcher.stop()
		watcher.join()

	# Show & Save final result
	generate_result()
	if clean:
		try:
			rmdir(directory_name)
		except OSError:
			print(directory_name + ' is not empty. Delete manually or check for artifacts.')

# format time
def get_time(elapsed):
	y = int(elapsed % 1 * 100)
	x = int(elapsed)
	hours = x / (60 * 60)
	x = x - (hours * 60 * 60)
	mins = x / 60
	x = x - (mins * 60)
	return "%02d:%02d:%02d.%2d" % (hours, mins, x, y)

# on_created event handler
def on_created(event):
	file_queue.put(event.src_path)

# ffmpeg command line
def generate_images():
	global rate
	rate_opt = ' '
	if not rate == '':
		rate_opt = ',fps=' + str(rate) + ' '
	cmd = 'ffmpeg -i ' + in_file + ' -vf scale=-1:144' + rate_opt + join(directory_name, 'img%05d.jpeg')
	print(cmd)
	result = system(cmd)
	if not result == 0:
		print('ffmpeg returned with exit code ' + str(result))
		exit(1)

# prints help info
def print_help():
	global resolutions
	print('Create from video file')
	print('\tmov-bar.py -i <video-input> [-d <images-directory-name>]')
	print('Create from directory of images')
	print('\tmov-bar.py -d <images-directory-name>')
	print('Extra options:')
	r_values = resolutions.keys()
	r_values.sort(reverse=True, key=int)
	r_sizes = '|'.join(r_values)
	print('\tResolution Quality: -q [' + r_sizes + ']')
	print('\tOutput file: -o <filename>')
	print('\tThread count: -t <num_threads>')
	print('\tFrames Per Second: -r <frame-rate>')
	print('\tDelete generated image files: -c')
	print('\tLength (in inches): -l <lengtgh>')
	print('\tWidth/Height (in inches): -w <width>')
	print('\tAdd name to image output: -n <text>')

# creates the final image
def visualize_colors(colors, height=50, length=300):
	rect = np.zeros((height, length, 3), dtype=np.uint8)
	start = 0
	percent = 1.0 / len(colors)
	for color in colors:
		end = start + (percent * length)
		cv2.rectangle(rect, (int(start), 0), (int(end), height), color[0], -1)
		start = end
	return rect

# gets the id of the file name to ensure the colors are in order
def get_id(file):
	return int(basename(file)[3:-5])

# gets the most common colors in a list of images
def process_images(index):
	global colors
	global directory_name
	global resolution
	global counts
	global file_queue
	global gen_id
	global clean

	# run while images are getting generated or are in queue
	while gen_id != 0 or not file_queue.empty():
		# get file to process
		f = ""
		try:
			f = file_queue.get_nowait()
		except Queue.Empty:
			continue
		# Load image and convert to a list of pixels
		image = None
		try:
			_ = io.imread(f)
			image = cv2.imread(f)
			image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		except:
			#print("error with " + f)
			file_queue.put(f)
			file_queue.task_done()
			continue
		reshape = image.reshape((image.shape[0] * image.shape[1], 3))

		# Find and display most dominant colors
		cluster = KMeans(n_clusters=1).fit(reshape)
		id = get_id(f)
		color = cluster.cluster_centers_.astype('uint8').tolist()[0]
		colors.append((color, id))
		counts[index] += 1
		if clean:
			remove(f)
		file_queue.task_done()

def output_csv():
	with open(out_file + '.csv', 'w') as f:
		writer = csv.writer(f, delimiter=',')
		for color in colors:
			row = color[0]
			writer.writerow(row)

def generate_from_csv():
	global colors
	with open(in_file) as f:
		reader = csv.reader(f, delimiter=',')
		row_num = 1
		for row in reader:
			color = [int(row[0]), int(row[1]), int(row[2])]
			colors.append((color, row_num))
			row_num += 1
	colors.sort(key = lambda x: x[1])
	visualize = visualize_colors(colors, resolution[1], resolution[0])
	visualize = cv2.cvtColor(visualize, cv2.COLOR_RGB2BGR)
	visualize = add_title(visualize)
	cv2.imwrite(out_file, visualize)
	if show:
		cv2.imshow(out_file, visualize)
		cv2.waitKey()
	exit(0)

# creates the result and outputs it
def generate_result():
	colors.sort(key = lambda x: x[1])
	visualize = visualize_colors(colors, resolution[1], resolution[0])
	visualize = cv2.cvtColor(visualize, cv2.COLOR_RGB2BGR)
	output_csv()
	visualize = add_title(visualize)
	cv2.imwrite(out_file, visualize)
	if show:
		cv2.imshow(out_file, visualize)
		cv2.waitKey()

def add_title(img):
	global title
	fonts = [
		cv2.FONT_HERSHEY_SIMPLEX,
		cv2.FONT_HERSHEY_PLAIN,
		cv2.FONT_HERSHEY_DUPLEX,
		cv2.FONT_HERSHEY_COMPLEX,
		cv2.FONT_HERSHEY_TRIPLEX,
		cv2.FONT_HERSHEY_COMPLEX_SMALL,
		cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
		cv2.FONT_HERSHEY_SCRIPT_COMPLEX
	]
	if title != "":
		h,w,c = img.shape
		font = fonts[0]
		# change this if text isn't aligned
		mult = 10
		char_spacing = 20*mult
		return cv2.putText(img, title.upper(), (w-(len(title * char_spacing)), h-10), font, 1*mult, (255, 255, 255), 3)
	return img
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print('Error: invalid number of args')
		print_help()
		exit(2)
	main(sys.argv[1:])
