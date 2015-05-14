#include <AccelStepper.h>
#include <SPI.h>
#include "Adafruit_BLE_UART.h"

// Connect CLK/MISO/MOSI to hardware SPI
// e.g. On UNO & compatible: CLK = 13, MISO = 12, MOSI = 11
#define BLE_SPI_CLK  13
#define BLE_SPI_MISO 12
#define BLE_SPI_MOSI 11
    
#define BLE_REQ 10
#define BLE_RST 9
#define BLE_RDY 2     // This should be an interrupt pin, on Uno thats #2 or #3

#define CAMERA_SHUTTER_DIG_OUT 8   // Hold high for 1 second, takes photo when it goes low

// Motor Pins
//    MS1  MS2  MS3
//     0    0    0  Full Step
//     1    0    0  Half Step
//     0    1    0  Quarter Step
//     1    1    0  Eighth Step
//     1    1    1  Sixteenth Step


#define MOTOR_MS1_DIG_OUT  7
#define MOTOR_MS2_DIG_OUT  6
#define MOTOR_MS3_DIG_OUT  5

#define MOTOR_STEP_DIG_OUT 4
#define MOTOR_DIR_DIG_OUT  3

#define MOTOR_NOT_ENABLE_DIG_OUT A2

// Other Pins
#define THERM_LASER_SENS_ANALOG_IN A5    // The thermal switch

#define LED_GREEN_DIG_OUT        A3
#define LED_RED_DIG_OUT          A4


#define DEBOUNCE_LIMIT 100
#define JOG_FINISHED_CODE 0


// The stepper motor object.
AccelStepper Stepper(AccelStepper::DRIVER, MOTOR_STEP_DIG_OUT,  MOTOR_DIR_DIG_OUT);

// The Blue Tooth serial object and status.
Adafruit_BLE_UART BTLEserial = Adafruit_BLE_UART(BLE_REQ, BLE_RDY, BLE_RST);

aci_evt_opcode_t gLastStatus = ACI_EVT_DISCONNECTED;
aci_evt_opcode_t gStatus = ACI_EVT_DISCONNECTED;

// Change to enum, but then we need header file.
#define LED_OFF 0
#define LED_GREEN 1
#define LED_AMBER 2
#define LED_RED 3

// For now we just have a "max 32 positions" array that we can
// remotely reset/add to, step though, etc.
int gPositionArray[32];
int gPositionArrayMax = sizeof(gPositionArray)/sizeof(int);
int gPositionArraySize = 0;
int gPositionArrayIndex = -1;

unsigned long gLastTimeSignalFired;
boolean gWaitingForThermalFalling;

void setup(void)
{ 
  Serial.begin(9600);
  Serial.println(F("BTAxisStepperPCBV1"));
  
  pinMode(LED_GREEN_DIG_OUT, OUTPUT);
  pinMode(LED_RED_DIG_OUT, OUTPUT);
  
  //pinMode(LIMIT_SWITCH_NEAR_DIG_IN, INPUT);
  //pinMode(LIMIT_SWITCH_FAR_DIG_IN, INPUT);
  
  pinMode(MOTOR_NOT_ENABLE_DIG_OUT, OUTPUT);
  pinMode(MOTOR_MS1_DIG_OUT, OUTPUT);
  pinMode(MOTOR_MS2_DIG_OUT, OUTPUT);
  pinMode(MOTOR_MS3_DIG_OUT, OUTPUT);
  pinMode(MOTOR_STEP_DIG_OUT, OUTPUT);
  pinMode(MOTOR_DIR_DIG_OUT, OUTPUT);
  // Don't bother setting the aux pins.
  
  // Enabled with 1/32 step
  digitalWrite(MOTOR_NOT_ENABLE_DIG_OUT, LOW);
  digitalWrite(MOTOR_MS1_DIG_OUT, HIGH);
  digitalWrite(MOTOR_MS2_DIG_OUT, HIGH);
  digitalWrite(MOTOR_MS3_DIG_OUT, HIGH);
  
  // Display Amber until we connect via Blue Tooth.
  setLed(LED_AMBER);
 
  // AccelStepper doesn't seem to be able to go above 800 probably 
  // because it's using millis() We should eventually tune these values
  // so we can get the best speed out of the rig.
  Stepper.setPinsInverted(true);
  Stepper.setMaxSpeed(2000);
  Stepper.setAcceleration(3000);
  Stepper.setCurrentPosition(0);

  gLastTimeSignalFired = 0;
  gWaitingForThermalFalling = false;
  BTLEserial.begin();
}

void acknowlageBLE(void)
{  
  sendResponseStringBT(&String(""));
}

void setLed(char ledState)
{
  digitalWrite(LED_GREEN_DIG_OUT, (ledState == LED_GREEN || ledState == LED_AMBER) ? HIGH : LOW);
  digitalWrite(LED_RED_DIG_OUT, (ledState == LED_RED || ledState == LED_AMBER) ? HIGH : LOW);
}

void sendThermalSensorValue(boolean isResponse)
{
  int thermalValue =  averagedThermalReading();
  if (isResponse) {
    sendResponseStringBT(&String("TEMP " + String(thermalValue)));
  } else {
    sendStringBT(&String("TEMP " + String(thermalValue)));
  }
  Serial.println(String(thermalValue).c_str());
}

void sendStepperPosition()
{
  sendStringBT(&String("POS " + String(Stepper.currentPosition())));
}

void blePoll()
{
  // Tell the nRF8001 to do whatever it should be working on.
  BTLEserial.pollACI();
  
  // Ask what is our current status is
  gStatus = BTLEserial.getState();
  if (gStatus != gLastStatus) {
    // Send status changes out to the serial port for debugging.
    if (gStatus == ACI_EVT_DEVICE_STARTED) {
      Serial.println(F("* Advertising started"));
      setLed(LED_AMBER);
    }
    if (gStatus == ACI_EVT_CONNECTED) {
      Serial.println(F("* Connected"));
      setLed(LED_GREEN);
      Serial.println(F("Done Sending State"));
    }
    if (gStatus == ACI_EVT_DISCONNECTED) {
      Serial.println(F("* Disconnected or advertising timed out"));
      setLed(LED_AMBER);
    }
    gLastStatus = gStatus;
  }
}

unsigned char blockingReadUnsignedChar()
{
    blePoll();  
    while (!(gStatus == ACI_EVT_CONNECTED && BTLEserial.available())) {
      blePoll();
    }
    return BTLEserial.read();
}

int blockingReadInt()
{
  unsigned char digit = blockingReadUnsignedChar();
  int value = 0;
  int postMultiply = (digit == '-') ? -1 : 1;

  // Right now the '-' code doesn't seem to work. Not sure why.
  // The '-' doesn't arrive.  We might be screwing it up on the app end of things.
  if (digit == '-') {
    digit = blockingReadUnsignedChar();
  }

  // Primative a to i for units, etc.
  while (digit >= '0' && digit <= '9') {
    value = value*10 + (digit - '0');
    digit = blockingReadUnsignedChar();
  } 
  return value*postMultiply;
}

void sendStringBT(String *s)
{
    if (gStatus != ACI_EVT_CONNECTED) {
      return;
    }
  
    uint8_t sendbuffer[32];
    s->getBytes(sendbuffer, 32);
    char sendbuffersize = min(32, s->length());
     BTLEserial.write(sendbuffer, sendbuffersize);
     blePoll();
}

void sendResponseStringBT(String *s)
{
 if (gStatus != ACI_EVT_CONNECTED) {
      return;
    }

    uint8_t sendbuffer[33];
    sendbuffer[0] = '*';
    s->getBytes(&(sendbuffer[1]), 32);
    char sendbuffersize = min(33, s->length() + 1);
     BTLEserial.write(sendbuffer, sendbuffersize);
     blePoll();
}

// The stepper motor produces a lot of noise
// so we average 16 readings to try and smooth out 
// the worst of it.  If you just read this drectly it
// triggers all the time.
int averagedThermalReading()
{
  int i;
  int value = 0;
  for (i=0; i<16; ++i) {
    value += analogRead(THERM_LASER_SENS_ANALOG_IN);
  }
  return value/16;
}

boolean waitForThermalSwitchOrBTCommand()
{
  int t1 = averagedThermalReading();
  int t0 = t1;
  int dt = 0;
  
  while (!BTLEserial.available()) {
    t0 = t1;
    t1 = averagedThermalReading();

    dt = t1 - t0;

    Serial.println(t1);
    if (dt >= 3 && !gWaitingForThermalFalling) {
      // We use a global flag so it persists between calls to this.
      gWaitingForThermalFalling = true;
      Serial.print("fire");
      return true;
    } if (dt <= 0 ) {
      gWaitingForThermalFalling = false;
    }

    // We only sample 5 times a second, so we spend the rest of the time
    // looking for BLE interruption.
    unsigned long nextSampleTime = millis() + 200;
    while (millis() < nextSampleTime) {
      blePoll();
      if (BTLEserial.available()) {
	break;
      }
    }
  }
  return false;
}

void signalFired()
{
  unsigned long curMillis = millis();
  // If the last time the thermal signal fired was less than a second ago, we assume 
  // this is a miss-fire and set the LED to red.
  if (curMillis - gLastTimeSignalFired < 1000) {
    setLed(LED_RED);
  } else {
    // Otherwise signal with green.
    setLed(LED_GREEN);
  }
  gLastTimeSignalFired = curMillis;
}

void runThermalSerialTest()
{
  int t1 = averagedThermalReading();
  int t0 = t1;
  int dt = 0;
  
  while (1) {
    t0 = t1;
    t1 = averagedThermalReading();

    dt = t1 - t0;

    Serial.print("value: ");
    Serial.print(t1);
    Serial.print(" dt: ");
    Serial.println(dt);
    delay(200);
    if (dt >= 3 && !gWaitingForThermalFalling) {
      signalFired();
      gWaitingForThermalFalling = true;
      Serial.println("FIRE");
    } if (dt <= 0 ) {
      gWaitingForThermalFalling = false;
    }

    unsigned long curMillis = millis();

    // After having at least one second of not firing we clear the led.
    if (curMillis - gLastTimeSignalFired > 1000) {
      setLed(LED_OFF);
    }
  }
}

void sequenceLoop()
{
  char commandChar = 0;

  while (gPositionArrayIndex < gPositionArraySize) {
    Serial.print("    sequence to ");
    Serial.println(gPositionArray[gPositionArrayIndex]);

    // Report all the info for this step, then run to the new position.
    sendThermalSensorValue(false);
    sendStepperPosition();
    sendStringBT(&String("RUN " + String(gPositionArrayIndex)));
    
    Stepper.runToNewPosition(gPositionArray[gPositionArrayIndex]);

    // If we got some sort of BT command.
    if (!waitForThermalSwitchOrBTCommand()) {
      commandChar = (char)blockingReadUnsignedChar();
      Serial.print("Got ");
      Serial.println(commandChar);

      // Inside the sequence loop the commands are n-next, p-previous, q-quit.
      if (commandChar == 'p') {
	if (gPositionArrayIndex > 0) {
	  acknowlageBLE();
	  gPositionArrayIndex--;
	} else {
	  sendResponseStringBT(&String("ignored"));
	  Serial.println("  Ignoring");
	}
      } else if (commandChar == 'n') {
	if (gPositionArrayIndex + 1 < gPositionArraySize) {
	  acknowlageBLE();
	  gPositionArrayIndex++;
	} else {
	  sendResponseStringBT(&String("ignoring"));
	  Serial.println("  Ignoring");
	}
      } else if (commandChar == 'q') {
	acknowlageBLE();
	return;
      }
    } else {
      sendStringBT(&String("THERM"));
      // If the thermal trip went off.
      gPositionArrayIndex++;
    }
  }
}

void commandLoop()
{
  boolean done = false;
  char commandChar = 0;
  
  while (!done) {
    blePoll();

    commandChar = (char)blockingReadUnsignedChar();
    Serial.print("Got ");
    Serial.println(commandChar);

    if (commandChar == 'x') {
      // x means kill off our position array.
      gPositionArraySize = 0;
      gPositionArrayIndex = -1;
      acknowlageBLE();
    } else if (commandChar == 'a') {
      // a means add a position to our position array.
      int position = (int)blockingReadInt();
      Serial.print("got position ");
      Serial.println(position);
      if (gPositionArraySize < gPositionArrayMax - 1) {
	gPositionArray[gPositionArraySize++] = position;
	acknowlageBLE();
      } else {
	sendResponseStringBT(&String("tomany"));
	Serial.println("error too many positions");
      }
    } else if (commandChar == 's') {
      // s means start going though the position sequence.
      gPositionArrayIndex = 0;
      acknowlageBLE();
      sendStringBT(&String("RUN " + String(gPositionArrayIndex)));
      sendThermalSensorValue(false);
      Stepper.setCurrentPosition(0);
      sequenceLoop();
    } else if (commandChar == 't') {
      sendThermalSensorValue(true);      
    } else {
      acknowlageBLE();
    }
  }
}

void loop()
{
  //  runThermalSerialTest();
    commandLoop();
}

