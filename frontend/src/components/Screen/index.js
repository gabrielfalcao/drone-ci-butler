import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";

export default function Screen(props) {
  return (
    <Container style={{ paddingTop: "4rem" }}>
      <Row className="justify-content-md-center">
        <Col xs> </Col>
        <Col md="auto">{props.children}</Col>
        <Col xs> </Col>
      </Row>
    </Container>
  );
}
