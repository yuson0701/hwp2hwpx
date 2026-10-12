import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import kr.dogfoot.hwplib.object.HWPFile;
import kr.dogfoot.hwplib.object.bodytext.paragraph.Paragraph;
import kr.dogfoot.hwplib.object.bodytext.paragraph.lineseg.LineSegItem;
import kr.dogfoot.hwplib.tool.blankfilemaker.BlankFileMaker;
import kr.dogfoot.hwplib.writer.HWPWriter;
public class XmlBoundaryRegression {
 public static void main(String[] a)throws Exception {
  HWPFile h=BlankFileMaker.make();
  String name=new String(Files.readAllBytes(Paths.get(a[1])),StandardCharsets.UTF_8);
  h.getDocInfo().getHangulFaceNameList().get(0).setName(name);
  Paragraph p=h.getBodyText().getSectionList().get(0).getParagraph(0);
  String body=new String(Files.readAllBytes(Paths.get(a[2])),StandardCharsets.UTF_8);
  if(p.getText()==null)p.createText();
  for(int i=0;i<body.length();i++)p.getText().addNewNormalChar().setCode(body.charAt(i));
  p.getText().addString("");
  if(a.length>3){p.createLineSeg();LineSegItem l=p.getLineSeg().addNewLineSegItem();l.setTextStartPosition(999999);l.setLineHeight(-1);l.setSegmentWidth(-1);}
  HWPWriter.toFile(h,a[0]);
 }
}
