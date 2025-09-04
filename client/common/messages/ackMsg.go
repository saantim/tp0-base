package messages

type AckMsg struct {
	result bool
}

const (
	AckMsgLen        = HeaderLen + AckMsgPayloadLen
	AckMsgPayloadLen = 1
)

// GetType returns the message type identifier for AckMsg.
func (a *AckMsg) GetType() MsgType {
	return AckMsgType
}

// SuccessResult returns the result of the operation.
// Returns true if the operation was successful, false otherwise.
func (a *AckMsg) SuccessResult() bool {
	return a.result
}
