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

int pressPwr1 = 38;
int pressPwr2 = 42;
int pressPwr3 = 46;

int pressHigh = A8;
int pressLow = A10;
int pressHighLow = A12;

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

  pinMode(pressPwr1, OUTPUT);
  pinMode(pressPwr2, OUTPUT);
  pinMode(pressPwr3, OUTPUT);
  pinMode(pressHigh, INPUT);
  pinMode(pressLow, INPUT);
  pinMode(pressHighLow, INPUT);
  
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
  
  digitalWrite(pressPwr1, HIGH);
  digitalWrite(pressPwr2, HIGH);
  digitalWrite(pressPwr3, HIGH);
}

void loop() {
  String input;
  if (Serial.available()) { // only run through loop if data has been sent
    input = Serial.readString(); // read the incoming data
    if (input == "normal_operation_v9") {
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

      Serial.println("normal_operation_v9");
    }
    else if (input == "normal_operation_v8") {
      // Normal operation while running the mass spec
      digitalWrite(LED_BUILTIN, LOW);
      digitalWrite(v1, LOW);
      digitalWrite(v2, LOW);
      digitalWrite(v3, HIGH);
      digitalWrite(v4, LOW);
      digitalWrite(v5, HIGH);
      digitalWrite(v6, LOW);
      digitalWrite(v7, LOW);
      digitalWrite(v8, HIGH);
      digitalWrite(v9, LOW);

      Serial.println("normal_operation_v8");
    }
    else if (input == "seawater_in") {
      // Filling an empty reservoir
      digitalWrite(v1, LOW); // DI Water
      digitalWrite(v2, HIGH); // Seawater
      digitalWrite(v3, LOW);
      digitalWrite(v4, LOW);
      digitalWrite(v5, LOW);
      digitalWrite(v6, LOW);
      digitalWrite(v7, HIGH);
      digitalWrite(v8, HIGH);
      digitalWrite(v9, LOW);
      
      Serial.println("seawater_in");
    }
    else if (input == "di_water_in") {
      // Filling or flushing an empty reservoir
      digitalWrite(LED_BUILTIN, HIGH);
      digitalWrite(v1, HIGH); // DI Water
      digitalWrite(v2, LOW); // Seawater
      digitalWrite(v3, LOW);
      digitalWrite(v4, LOW);
      digitalWrite(v5, LOW);
      digitalWrite(v6, LOW);
      digitalWrite(v7, HIGH);
      digitalWrite(v8, HIGH);
      digitalWrite(v9, LOW);
      
      Serial.println("di_water_in");
    }
    else if (input == "emptying_fr") {
      // Emptying the fluid reservoir
      // Fluid is pushed out of reservoir by gas
      digitalWrite(v1, HIGH);
      digitalWrite(v2, LOW);
      digitalWrite(v3, HIGH);
      digitalWrite(v4, HIGH);
      digitalWrite(v5, LOW);
      digitalWrite(v6, LOW);
      digitalWrite(v7, LOW);
      digitalWrite(v8, LOW);
      digitalWrite(v9, LOW);
      
      Serial.println("emptying_fr");
    }
    else if (input == "release_press") {
      // Releasing pressure from the system
      digitalWrite(LED_BUILTIN, LOW);
      digitalWrite(v1, LOW);
      digitalWrite(v2, LOW);
      digitalWrite(v3, LOW);
      digitalWrite(v4, LOW);
      digitalWrite(v5, LOW);
      digitalWrite(v6, LOW);
      digitalWrite(v7, LOW);
      digitalWrite(v8, HIGH);
      digitalWrite(v9, LOW);
      
      Serial.println("release_press");
    }
    else if (input == "reset") {
      // setting the system back into startup mode to turn off all solenoid valves and other pins
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
        
        digitalWrite(pressPwr1, LOW);
        digitalWrite(pressPwr2, LOW);
        digitalWrite(pressPwr3, LOW);

        Serial.println("reset");
    }
    else if (input == "press") {
        digitalWrite(pressPwr1, HIGH);
        digitalWrite(pressPwr2, HIGH);
        digitalWrite(pressPwr3, HIGH);
        delay(100);
        String pressValues = "";
        int valHigh = analogRead(pressHigh);
        int valLow = analogRead(pressLow);
        int valHighLow = analogRead(pressHighLow);
        pressValues.concat(valHigh);
        pressValues.concat(", ");
        pressValues.concat(valLow);
        pressValues.concat(", ");
        pressValues.concat(valHighLow);
        
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
