package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-chaincode-go/shim"
	"github.com/hyperledger/fabric-protos-go/peer"
)

// SmartContract defines the chaincode structure
type SmartContract struct {
}

// SensorData represents air quality measurements
type SensorData struct {
	ID        string    `json:"id"`
	Timestamp time.Time `json:"timestamp"`
	PM25      float64   `json:"pm25"`
	PM10      float64   `json:"pm10"`
	CO2       float64   `json:"co2"`
	Latitude  float64   `json:"latitude"`
	Longitude float64   `json:"longitude"`
	Hash      string    `json:"hash"`
}

func (s *SmartContract) Init(stub shim.ChaincodeStubInterface) peer.Response {
	return shim.Success(nil)
}

func (s *SmartContract) Invoke(stub shim.ChaincodeStubInterface) peer.Response {
	function, args := stub.GetFunctionAndParameters()
	
	switch function {
	case "AddData":
		return s.AddData(stub, args)
	case "GetData":
		return s.GetData(stub, args)
	case "VerifyData":
		return s.VerifyData(stub, args)
	case "GetHistory":
		return s.GetHistory(stub, args)
	default:
		return shim.Error("Invalid function name")
	}
}

// AddData stores sensor reading with integrity hash
func (s *SmartContract) AddData(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	if len(args) != 1 {
		return shim.Error("Incorrect arguments. Expecting JSON sensor data")
	}

	var data SensorData
	err := json.Unmarshal([]byte(args[0]), &data)
	if err != nil {
		return shim.Error("Failed to parse sensor data")
	}

	// Generate composite key
	compositeKey, err := stub.CreateCompositeKey("Sensor~Timestamp", []string{data.ID, data.Timestamp.Format(time.RFC3339)})
	if err != nil {
		return shim.Error(err.Error())
	}

	// Calculate data hash
	hash := sha256.New()
	hash.Write([]byte(fmt.Sprintf("%v", data)))
	data.Hash = hex.EncodeToString(hash.Sum(nil))

	dataJSON, err := json.Marshal(data)
	if err != nil {
		return shim.Error(err.Error())
	}

	err = stub.PutState(compositeKey, dataJSON)
	if err != nil {
		return shim.Error(err.Error())
	}

	return shim.Success(nil)
}

// GetData retrieves sensor data by ID and timestamp range
func (s *SmartContract) GetData(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	if len(args) != 3 {
		return shim.Error("Requires sensor ID, start time, and end time")
	}

	resultsIterator, err := stub.GetStateByPartialCompositeKey("Sensor~Timestamp", []string{args[0]})
	if err != nil {
		return shim.Error(err.Error())
	}
	defer resultsIterator.Close()

	var buffer bytes.Buffer
	buffer.WriteString("[")

	for resultsIterator.HasNext() {
		response, err := resultsIterator.Next()
		if err != nil {
			return shim.Error(err.Error())
		}

		var data SensorData
		err = json.Unmarshal(response.Value, &data)
		if err != nil {
			return shim.Error(err.Error())
		}

		// Check timestamp range
		if data.Timestamp.Format(time.RFC3339) >= args[1] && 
			data.Timestamp.Format(time.RFC3339) <= args[2] {
			buffer.Write(response.Value)
			buffer.WriteString(",")
		}
	}

	if buffer.Len() > 1 {
		buffer.Truncate(buffer.Len() - 1)
	}
	buffer.WriteString("]")

	return shim.Success(buffer.Bytes())
}

// VerifyData checks data integrity using stored hash
func (s *SmartContract) VerifyData(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	if len(args) != 1 {
		return shim.Error("Requires composite key")
	}

	dataBytes, err := stub.GetState(args[0])
	if err != nil {
		return shim.Error(err.Error())
	}

	var data SensorData
	err = json.Unmarshal(dataBytes, &data)
	if err != nil {
		return shim.Error(err.Error())
	}

	originalHash := data.Hash
	hash := sha256.New()
	hash.Write([]byte(fmt.Sprintf("%v", data)))
	currentHash := hex.EncodeToString(hash.Sum(nil))

	if originalHash != currentHash {
		return shim.Error("Data tampering detected")
	}

	return shim.Success([]byte("Data integrity verified"))
}

// GetHistory returns audit trail for a data entry
func (s *SmartContract) GetHistory(stub shim.ChaincodeStubInterface, args []string) peer.Response {
	if len(args) != 1 {
		return shim.Error("Requires composite key")
	}

	historyIterator, err := stub.GetHistoryForKey(args[0])
	if err != nil {
		return shim.Error(err.Error())
	}
	defer historyIterator.Close()

	var buffer bytes.Buffer
	buffer.WriteString("[")

	for historyIterator.HasNext() {
		response, err := historyIterator.Next()
		if err != nil {
			return shim.Error(err.Error())
		}

		buffer.WriteString(fmt.Sprintf(
			`{"txid":"%s", "value":%s, "timestamp":"%s", "is_delete":"%t"}`,
			response.TxId,
			string(response.Value),
			response.Timestamp.AsTime().Format(time.RFC3339),
			response.IsDelete,
		))
		buffer.WriteString(",")
	}

	if buffer.Len() > 1 {
		buffer.Truncate(buffer.Len() - 1)
	}
	buffer.WriteString("]")

	return shim.Success(buffer.Bytes())
}

func main() {
	err := shim.Start(new(SmartContract))
	if err != nil {
		fmt.Printf("Error starting chaincode: %s", err)
	}
}
