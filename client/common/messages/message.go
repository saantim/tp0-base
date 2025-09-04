package messages

type Message interface {
	GetType()
	PayloadLen()
}
type MsgType uint8

const (
	HeaderLen = 1

	BetMsgType MsgType = 1
	AckMsgType MsgType = 2
)

// BuildAckMsg creates an AckMsg from raw bytes.
func BuildAckMsg(msg []byte) AckMsg {
	result := msg[1] == 1
	return AckMsg{result: result}
}
