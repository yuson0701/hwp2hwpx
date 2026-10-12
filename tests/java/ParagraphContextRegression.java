import kr.dogfoot.hwplib.object.HWPFile;
import kr.dogfoot.hwplib.object.bodytext.paragraph.Paragraph;
import kr.dogfoot.hwplib.object.bodytext.control.ControlTable;
import kr.dogfoot.hwplib.tool.blankfilemaker.BlankFileMaker;
import kr.dogfoot.hwplib.writer.HWPWriter;

public class ParagraphContextRegression {
    public static void main(String[] args) throws Exception {
        HWPFile h = BlankFileMaker.make();
        ControlTable outer = NestedTableRegression.table(
            h.getBodyText().getSectionList().get(0).getParagraph(0), 3, 100, 1);
        Paragraph p = outer.getRowList().get(0).getCellList().get(0)
            .getParagraphList().getParagraph(0);
        p.getText().addString("BETWEEN_TABLES");
        NestedTableRegression.table(p, 1, 200, 0);
        p.getText().addString("AFTER_TABLES");
        HWPWriter.toFile(h, args[0]);
    }
}
