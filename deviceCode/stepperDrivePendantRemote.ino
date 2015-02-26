#include <AccelStepper.h>
#include <SPI.h>

// For DVV8825 Stepper Driver
// MS1  MS2  MS3
//  0    0    0  Full Step
//  1    0    0  Half Step
//  0    1    0  Quarter Step
//  1    1    0  Eighth Step
//  0    0    1  Sixteenth Step
//  1    0    1  Thirtysecond Step
//  0    1    1      "
//  1    1    1      "

#define MOTOR_NOT_ENABLE_DIG_OUT A2

#define MOTOR_MS1_DIG_OUT  7
#define MOTOR_MS2_DIG_OUT  6
#define MOTOR_MS3_DIG_OUT  5

#define MOTOR_STEP_DIG_OUT 4
#define MOTOR_DIR_DIG_OUT  3

// Switches 
#define BACK_SWITCH_DIG_IN A0
#define FORWARD_SWITCH_DIG_IN  A1


// The stepper motor object.
AccelStepper Stepper(AccelStepper::DRIVER, MOTOR_STEP_DIG_OUT,  MOTOR_DIR_DIG_OUT);


void setup(void)
{ 
  Serial.begin(9600);
  Serial.println(F("aAxisStepperDriver3"));
  
  // pinMode(BACK_SWITCH_DIG_IN, INPUT_PULLUP);
  // pinMode(FORWARD_SWITCH_DIG_IN, INPUT_PULLUP);
  pinMode(BACK_SWITCH_DIG_IN, INPUT);
  pinMode(FORWARD_SWITCH_DIG_IN, INPUT);
  
  // Because these are analog pins, we write high to get the pull up
  // I don't know if INPUT_PULLUP works with those it doesn't mention 
  // that on the web site.
  digitalWrite(BACK_SWITCH_DIG_IN, HIGH);
  digitalWrite(FORWARD_SWITCH_DIG_IN, HIGH);
  
  pinMode(MOTOR_NOT_ENABLE_DIG_OUT, OUTPUT);
  pinMode(MOTOR_MS1_DIG_OUT, OUTPUT);
  pinMode(MOTOR_MS2_DIG_OUT, OUTPUT);
  pinMode(MOTOR_MS3_DIG_OUT, OUTPUT);
  pinMode(MOTOR_STEP_DIG_OUT, OUTPUT);
  pinMode(MOTOR_DIR_DIG_OUT, OUTPUT);
  
  // Enabled with 1/32 step
  digitalWrite(MOTOR_NOT_ENABLE_DIG_OUT, LOW);
  digitalWrite(MOTOR_MS1_DIG_OUT, HIGH);
  digitalWrite(MOTOR_MS2_DIG_OUT, HIGH);
  digitalWrite(MOTOR_MS3_DIG_OUT, HIGH);
 
  // AccelStepper can not go supper fast probably 
  // because it's using millis()
  Stepper.setPinsInverted(true);
  Stepper.setMaxSpeed(2000);
  Stepper.setAcceleration(3000);
  Stepper.setCurrentPosition(0);
}

 
void loop()
{
  int forwardValue = digitalRead(FORWARD_SWITCH_DIG_IN);
  int backValue = !digitalRead(BACK_SWITCH_DIG_IN);
  
  while (forwardValue == HIGH && backValue == HIGH) {
    delay(100);
    forwardValue = digitalRead(FORWARD_SWITCH_DIG_IN);
    backValue = !digitalRead(BACK_SWITCH_DIG_IN);
  }
  
  if (forwardValue == LOW) {
    // got 1/16 of the way around
    Stepper.setCurrentPosition(0);
    Stepper.runToNewPosition(400*2);
  } else if (backValue == LOW) {
    // Go 1/2 way around
    Stepper.setCurrentPosition(400*16);
    Stepper.runToNewPosition(0);
  }
}

