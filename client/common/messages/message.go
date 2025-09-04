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

	BetMsgType      MsgType = 1
	AckMsgType      MsgType = 2
	BetBatchMsgType MsgType = 3
)

// BuildAckMsg creates an AckMsg from raw bytes.
func BuildAckMsg(msg []byte) AckMsg {
	result := msg[2] == 1
	return AckMsg{result: result}
}
