#include <Arduino.h>

int v1 = 31;
int v2 = 33;
int v3 = 35;
int v4 = 37;
int v5 = 39;
int v6 = 41;
int v7 = 43;  
int v8 = 45;
int v9 = 47;

int flushPin = 52;

int press1 = A8;
int press2 = A9;
int press3 = A10;

void setup() {
  Serial.begin(9600); // set the baud rate
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  //pinMode(pin_number, mode)
  pinMode(v1, OUTPUT);
  pinMode(v2, OUTPUT);
  pinMode(v3, OUTPUT);
  pinMode(v4, OUTPUT);
  pinMode(v5, OUTPUT);
  pinMode(v6, OUTPUT);
  pinMode(v7, OUTPUT);
  pinMode(v8, OUTPUT);
  pinMode(v9, OUTPUT);
  pinMode(flushPin, OUTPUT);
  //make all solenoid valves closed
  digitalWrite(v1, LOW);
  digitalWrite(v2, LOW);
  digitalWrite(v3, LOW);
  digitalWrite(v4, LOW);
  digitalWrite(v5, LOW);
  digitalWrite(v6, LOW);
  digitalWrite(v7, LOW);
  digitalWrite(v8, LOW);
  digitalWrite(v9, LOW);
  digitalWrite(flushPin, LOW);
  // run through any necessary health checks
  //?
  
  // check solenoid valves and flush pump
  //?
  
  //Serial.println('1'); // print "Ready" once
}

void loop() {
  String input;
  if (Serial.available()) { // only run through loop if data has been sent
    input = Serial.readString(); // read the incoming data
    if (input == "valves 1") {
      // Normal operation while running the mass spec
            
      digitalWrite(LED_BUILTIN, LOW);
      digitalWrite(v1, LOW);
      digitalWrite(v2, LOW);
      digitalWrite(v3, HIGH);
      digitalWrite(v4, LOW);
      digitalWrite(v5, HIGH);
      digitalWrite(v6, LOW);
      digitalWrite(v7, LOW);
      digitalWrite(v8, LOW);
      digitalWrite(v9, HIGH);

      Serial.println("valves 1");
    }
    else if (input == "valves 2") {
      // Filling an empty reservoir
      
      digitalWrite(LED_BUILTIN, HIGH);
      // v1 and v2 change depending on what you're filling with
      digitalWrite(v1, LOW); // DI Water
      digitalWrite(v2, HIGH); // Seawater
      digitalWrite(v3, LOW);
      digitalWrite(v4, LOW);
      digitalWrite(v5, LOW);
      digitalWrite(v6, LOW);
      digitalWrite(v7, HIGH);
      digitalWrite(v8, HIGH);
      digitalWrite(v9, LOW);
      
      Serial.println("valves 2");
    }
    else if (input == "valves 3") {
      // Emptying the fluid reservoir
      // Fluid is pushed out of reservoir by gas
      // TODO do I need to turn that gas on?
      
      digitalWrite(LED_BUILTIN, HIGH);
      digitalWrite(v1, HIGH); // v1 and v2 change depending on what you're filling with
      digitalWrite(v2, LOW);
      digitalWrite(v3, HIGH);
      digitalWrite(v4, HIGH);
      digitalWrite(v5, LOW);
      digitalWrite(v6, LOW);
      digitalWrite(v7, LOW);
      digitalWrite(v8, LOW);
      digitalWrite(v9, LOW);
      
      Serial.println("valves 3");
    }
    else if (input == "press") {
        String pressValues = "";
        int val1 = analogRead(press1);
        int val2 = analogRead(press2);
        int val3 = analogRead(press3);
        pressValues.concat(val1);
        pressValues.concat(", ");
        pressValues.concat(val2);
        pressValues.concat(", ");
        pressValues.concat(val3);
        Serial.println(pressValues);
    }
    else if (input == "flushOn") {
      //turn on the pin that triggers the SSR
      digitalWrite(flushPin, HIGH);
      
      Serial.println("flushOn");
    }
    else if (input == "flushOff") {
      //turn on the pin that triggers the SSR
      digitalWrite(flushPin, LOW);
      
      Serial.println("flushOff");
    }
    else if (input == "?") {
      // Notifying controller that we're in a healthy state
      Serial.println("1");
    }
    else {
      Serial.println("F001");
    }
  }
  delay(100); // delay for 1/10 of a second
}
