package messages

import "github.com/op/go-logging"

type Message interface {
	GetType()
	PayloadLen()
}
type MsgType uint8

var log = logging.MustGetLogger("log")

const (
	HeaderLen = 2
	AgencyLen = 1

	BetMsgType         MsgType = 1
	AckMsgType         MsgType = 2
	BetBatchMsgType    MsgType = 3
	FinishBatchMsgType MsgType = 4
	AskWinnersMsgType  MsgType = 5
	WinnersMsgType     MsgType = 6
)

// BuildAckMsg creates an AckMsg from raw bytes.
func BuildAckMsg(msg []byte) AckMsg {
	result := msg[2] == 1
	return AckMsg{result: result}
}

// IsAckHeader checks if the header belongs to an AckMsg.
func IsAckHeader(header []byte) bool {
	return MsgType(header[0]) == AckMsgType
}

// IsWinnersHeader checks if the header belongs to a WinnersMsg.
func IsWinnersHeader(header []byte) bool {
	return MsgType(header[0]) == WinnersMsgType
}
