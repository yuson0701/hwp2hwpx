import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import kr.dogfoot.hwpxlib.writer.common.*;
import kr.dogfoot.hwpxlib.object.content.section_xml.SubList;
import kr.dogfoot.hwpxlib.commonstrings.Namespaces;
public class XmlAttributeRegression {
 public static void main(String[] a)throws Exception {
  String value="{\"name\":\"A&B <C> &quot;\"}\t\n\r";
  ElementWriterManager m=new ElementWriterManager();
  m.xsb().openElement("root").namespace(Namespaces.hp);
  SubList sub=new SubList();sub.metaTag(value);
  m.get(ElementWriterSort.SubList).write(sub);
  m.xsb().closeElement();
  Files.write(Paths.get(a[0]),m.xsb().toString().getBytes(StandardCharsets.UTF_8));
 }
}
