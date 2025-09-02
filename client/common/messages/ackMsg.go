package messages

type AckMsg struct {
	result bool
}

const (
	AckMsgLen        = HeaderLen + AckMsgPayloadLen
	AckMsgPayloadLen = 1
)

func (a *AckMsg) GetType() MsgType {
	return AckMsgType
}

func (a *AckMsg) SuccessResult() bool {
	return a.result
}
