import { Container, Row, Col } from "react-bootstrap";

export default function WebFrame(props) {
  return (
    <Container>
      <Row className="justify-content-md-center">
        <Col xs lg="2">
          {" "}
        </Col>
        <Col md="auto">{props.children}</Col>
        <Col xs lg="2">
          {" "}
        </Col>
      </Row>
    </Container>
  );
}

