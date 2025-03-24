/*
  Air Quality Sensor Firmware
  Reads PM2.5, PM10, CO2, Temperature/Humidity
  Transmits via LoRaWAN (868MHz)
*/

#include <LoRa.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <PMS.h>

// Configuration
#define LORA_FREQ 868E6  // EU frequency
#define BME280_ADDR 0x76
#define PMS_RX 16
#define PMS_TX 17

// Sensor Objects
Adafruit_BME280 bme;
PMS pms(Serial1);
PMS::DATA pmsData;

void setup() {
  Serial.begin(115200);
  
  // Initialize BME280
  if (!bme.begin(BME280_ADDR)) {
    Serial.println("BME280 not found!");
    while(1);
  }

  // Initialize PMS5003
  Serial1.begin(9600, SERIAL_8N1, PMS_RX, PMS_TX);
  pms.passiveMode();

  // Initialize LoRa
  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("LoRa init failed!");
    while(1);
  }
  LoRa.setTxPower(20);
}

void readSensors() {
  // Read Particulate Matter
  pms.wakeUp();
  delay(30);
  pms.requestRead();
  if (pms.readUntil(pmsData)) {
    float pm25 = pmsData.PM_AE_UG_2_5;
    float pm10 = pmsData.PM_AE_UG_10_0;
  } else {
    Serial.println("PMS5003 read failed");
  }
  pms.sleep();

  // Read BME280
  float temp = bme.readTemperature();
  float humidity = bme.readHumidity();
  float pressure = bme.readPressure() / 100.0;

  // Read MQ-135 (Analog)
  int mq135_raw = analogRead(34);
  float co2 = map(mq135_raw, 0, 4095, 400, 5000); // Calibration needed

  // Prepare LoRa Packet
  String payload = String(pm25) + "," + 
                   String(pm10) + "," +
                   String(co2) + "," + 
                   String(temp) + "," +
                   String(humidity);

  // Send via LoRa
  LoRa.beginPacket();
  LoRa.print(payload);
  LoRa.endPacket();

  Serial.println("Sent: " + payload);
  delay(30000);  // Sleep 30s between readings
}

void loop() {
  readSensors();
}
