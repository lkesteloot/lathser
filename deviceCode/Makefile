DEVICE     = attiny85
CLOCK      = 8000000
PROGRAMMER = usbtiny
PORT	   = /dev/tty.usbmodem1421
BAUD       = 19200
FILENAME   = laserDetector
COMPILE    = avr-gcc -Wall -Os -DF_CPU=$(CLOCK) -mmcu=$(DEVICE)

all: build upload

usb:
	ls /dev/cu.*

build:
	$(COMPILE) -c $(FILENAME).c -o $(FILENAME).o
	$(COMPILE) -o $(FILENAME).elf $(FILENAME).o
	avr-objcopy -j .text -j .data -O ihex $(FILENAME).elf $(FILENAME).hex
	avr-size --format=avr --mcu=$(DEVICE) $(FILENAME).elf

upload:
	avrdude -v -p $(DEVICE) -c $(PROGRAMMER) -b $(BAUD) -U flash:w:$(FILENAME).hex:i 

clean:
	rm $(FILENAME).o
	rm $(FILENAME).elf
	rm $(FILENAME).hex
