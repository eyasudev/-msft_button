/**
 * @file    main.ino
 * @author  Clifford Olawaiye (cliffordolawaiye@gmail.com)
 * @brief   esp32 firmware for the microsoft teams mute button project
 * @version 1.0
 * @date    2022-06-17
 * 
 * @copyright Copyright (c) 2022
 * 
 * @paragraph important-info Important information 
 * 
 *            Instructions: 
 *            1. Connect your swtich between SWITCH_PIN and GND
 * 
 *            Other info:
 *            1. A tool for generating UUIDs: https://www.uuidgenerator.net/, can 
 *                be used for generating BLE SERVICE IDs and CHARACTERISITICS include 
 *            2. See how to use the Button.h library here: https://www.arduino.cc/reference/en/libraries/button/
 */

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>
#include <Button.h>         

/** Globals: Switch */
#define LED_RGB 48
#define SWITCH_PIN 1
Button button1(SWITCH_PIN); 

/** Globals: BLE */
#define BLE_NAME "Teams mute button"
BLEServer *pServer = NULL;
BLECharacteristic * pTxCharacteristic;
bool deviceConnected = false;
bool oldDeviceConnected = false;
uint32_t tm_counter = 0;

#define SERVICE_UUID           "6E400001-B5A3-F393-E0A9-E50E24DCCA9E" 
#define CHARACTERISTIC_UUID_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


class MyServerCallbacks: public BLEServerCallbacks {

    void onConnect(BLEServer* pServer) {
      deviceConnected = true;
    };

    void onDisconnect(BLEServer* pServer) {
      deviceConnected = false;
    }
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
      std::string rxValue = pCharacteristic->getValue();

      if (rxValue.length() > 0) {
        Serial.println("*********");
        Serial.print("Received Value: ");
        for (int i = 0; i < rxValue.length(); i++)
          Serial.print(rxValue[i]);

        Serial.println();
        Serial.println("*********");
      }
    }
};


void setup_ble(){
    // Create the BLE Device
    BLEDevice::init(BLE_NAME);

    // Create the BLE Server
    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // Create the BLE Service
    BLEService *pService = pServer->createService(SERVICE_UUID);

    // Create a BLE Characteristic
    pTxCharacteristic = pService->createCharacteristic(
                                            CHARACTERISTIC_UUID_TX,
                                            BLECharacteristic::PROPERTY_NOTIFY
                                        );
                        
    pTxCharacteristic->addDescriptor(new BLE2902());

    BLECharacteristic * pRxCharacteristic = pService->createCharacteristic(
                                                CHARACTERISTIC_UUID_RX,
                                                BLECharacteristic::PROPERTY_WRITE
                                            );

    pRxCharacteristic->setCallbacks(new MyCallbacks());

    // Start the service
    pService->start();

    // Start advertising
    pServer->getAdvertising()->start();
    Serial.println("Waiting a client connection to notify...");

}

void setup(){
    /** Setup: switch */ 
    Serial.begin(115200);
    button1.begin();
    Serial.println("Hello there");

    /** Setup: BLE */ 
    setup_ble();
}

void loop(){

    /** Logic: Bluetooth */
    if (deviceConnected) {      
        //send data on every toggle or every 1 sec (100 counts of 10ms)
        if (button1.toggled() || !(tm_counter % 100)) {

            bool btn_ret =   button1.read();

            if (btn_ret == Button::PRESSED) Serial.println("Button 1 pressed");
            else Serial.println("Button 1 released");

            tm_counter=0; //reset counter
            
            //sends "teamsbtn:00" when pressed and "teamsbtn:01" when released
            char data_to_send[20] = "";
            snprintf(data_to_send, sizeof(data_to_send), "teamsbtn:%02d", btn_ret); 

            pTxCharacteristic->setValue((uint8_t*)data_to_send, strlen(data_to_send));
            pTxCharacteristic->notify();
        }

        tm_counter++;
        delay(10); // bluetooth stack will go into congestion, if too many packets are sent
    }

    // disconnecting
    if (!deviceConnected && oldDeviceConnected) {
        delay(500); // give the bluetooth stack the chance to get things ready
        pServer->startAdvertising(); // restart advertising
        Serial.println("start advertising");
        oldDeviceConnected = deviceConnected;
    }
    
    // connecting
    if (deviceConnected && !oldDeviceConnected) {
		    // do stuff here on connecting
        oldDeviceConnected = deviceConnected;
    }
}


